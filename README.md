# Serving_Framework
The proposed serving framework is built on top of vLLM (release version: 0.5.0 post1). <br>
All the adds-on by the framework are located in the folder `additional_designs`.

## Getting Started
1. Install the backbone system (vllm 0.5.0. post1) first. Following guidelines from https://github.com/vllm-project/vllm.
2. Insert the additional designs:
```
bash insert_designs.sh
```
3. Install the customized cuda kernels to support hybrid cache:
```
python python mixed_cache_setup.py build_ext --inplace
```
With all these steps completed, the necessary implementation for the new designs has been integrated into vLLM and is ready for use.

## Serving Simulation
Use OPT-13B as an example. <br>
Start the server side by:
```
python -m vllm.entrypoints.openai.api_server --model facebook/opt-13b --enforce-eager --disable-log-requests
```
After the server side is set up, start the client side code to simulate the request arrivals:
```
CUDA_VISIBLE_DEVICES="0" python gen_client_requests.py --model facebook/opt-13b --request-rate 3 --cv 1
```
