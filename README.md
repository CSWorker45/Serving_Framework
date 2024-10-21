# Serving_Framework
The proposed serving framework is built on top of vLLM (release version: 0.5.0 post1). <br>
All the adds-on by the framework are located in the folder `additional_designs`.

## Getting Started
1. Install the backbone system (vllm 0.5.0. post1) first. Following guidelines from https://github.com/vllm-project/vllm.
2. Insert the additional designs:
```
bash additional_designs/insert_designs.sh
```
3. Install the customized cuda kernels to support hybrid cache:
```
python additional_designs/mixed_cache_kernels/mixed_cache_setup.py build_ext --inplace
```
With all these steps completed, the necessary implementation for the new designs has been integrated into vLLM and is ready for use.

## Sample Serving Traces
Following `readme.md` from the folder `sample_requests_from_datasets` to sample requests to create a serving trace.
The sampled requests are automatically saved into `./sampled_datasets/` folder.

## Serving Simulation
Use OPT-13B as an example. <br>
Start the server side by:
```
python -m vllm.entrypoints.openai.api_server --model facebook/opt-13b --enforce-eager --disable-log-requests
```
After the server side is set up, start the client side code to simulate the request arrivals:
```
python gen_client_requests.py --model facebook/opt-13b --request-rate 3 --cv 1 --dataset sharegpt
```
Here is an exemplar serving result:<br>
<img width="360" alt="slo_result" src="https://github.com/user-attachments/assets/267b228d-e472-41a9-ad85-f320befde71d">
