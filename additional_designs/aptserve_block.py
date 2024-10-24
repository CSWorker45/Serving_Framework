"""Token blocks."""
import weakref
from collections import defaultdict
from typing import Dict, List

from vllm.utils import Device

_BLANK_TOKEN_ID = -1

DEFAULT_LAST_ACCESSED_TIME = -1

TokensBlock = List[int]


class BlockPool:
    """A pool of logical blocks.
    When requests come, we create a lot of logical blocks;
    when requests are done, we destroy a lot of logical blocks.
    It turns out that creating and destroying logical blocks can be expensive,
    especially for the `token_ids` field, which is a list of integers.
    To avoid this overhead, we use a pool to manage the logical blocks.
    When an old request is done and a new request comes, we can reuse the
    logical blocks from the old request to feed the new request.
    """

    def __init__(self) -> None:
        # block size to list of token blocks
        self.pool: Dict[int, List[TokensBlock]] = defaultdict(list)

    def alloc_block(self, block_size: int) -> TokensBlock:
        if block_size in self.pool and self.pool[block_size]:
            return self.pool[block_size].pop()
        return [_BLANK_TOKEN_ID] * block_size

    def del_block(self, block: TokensBlock) -> None:
        self.pool[len(block)].append(block)


_BLOCK_POOL = BlockPool()


class LogicalTokenBlock:
    """A block that stores a contiguous chunk of tokens from left to right.

    Logical blocks are used to represent the states of the corresponding
    physical blocks in the KV cache.
    """

    def __init__(
        self,
        block_number: int,
        block_size: int,
    ) -> None:
        self.block_number = block_number
        self.block_size = block_size

        self.token_ids = _BLOCK_POOL.alloc_block(block_size)
        # this finalizer is used to return the block to the pool when the object is deleted # noqa
        # NOTE: don't use __del__ because it cannot guarantee the order of finalization, # noqa
        # i.e. `self.token_ids` may be deleted before `self`, and we lose
        #  the opportunity to return the block to the pool
        self._finalizer = weakref.finalize(self, _BLOCK_POOL.del_block,
                                           self.token_ids)
        self.num_tokens = 0

    def is_empty(self) -> bool:
        return self.num_tokens == 0

    def get_num_empty_slots(self) -> int:
        return self.block_size - self.num_tokens

    def is_full(self) -> bool:
        return self.num_tokens == self.block_size

    def append_tokens(self, token_ids: List[int]) -> None:
        assert len(token_ids) <= self.get_num_empty_slots()
        curr_idx = self.num_tokens
        self.token_ids[curr_idx:curr_idx + len(token_ids)] = token_ids
        self.num_tokens += len(token_ids)

    def get_token_ids(self) -> List[int]:
        return self.token_ids[:self.num_tokens]

    def get_last_token_id(self) -> int:
        assert self.num_tokens > 0
        return self.token_ids[self.num_tokens - 1]


class PhysicalTokenBlock:
    """Represents the state of a block in the KV cache."""

    def __init__(
        self,
        device: Device,
        block_number: int,
        block_size: int,
        block_hash: int,
        num_hashed_tokens: int,
    ) -> None:
        self.device = device
        self.block_number = block_number
        self.block_size = block_size
        self.block_hash = block_hash
        self.num_hashed_tokens = num_hashed_tokens

        self.ref_count = 0
        #modification for hidden cache usage.
        #self.k_filled = False
        #self.v_filled = False
        self.last_accessed = DEFAULT_LAST_ACCESSED_TIME

        self.computed = False
    
    def __repr__(self) -> str:
        return (f'PhysicalTokenBlock(device={self.device}, '
                f'block_number={self.block_number}, '
                f'num_hashed_tokens={self.num_hashed_tokens}, '
                f'ref_count={self.ref_count}, '
                f'last_accessed={self.last_accessed}, '
                f'computed={self.computed})')


# Mapping: logical block number -> physical block.
BlockTable = List[PhysicalTokenBlock]
