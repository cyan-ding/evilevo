# Evo2 Inference Web API

A simple Flask API for running Evo2 inference via HTTP requests.

## Installation

```bash
pip install -r requirements.txt
```

## Running the API

```bash
python app.py
```

The API will start on `http://0.0.0.0:5000`

## Endpoints

### POST /inference

Run Evo2 inference with the provided parameters.

**Required Parameters:**
- `ckpt_dir` (string): Path to checkpoint directory containing pre-trained Evo2 model

**Optional Parameters:**
- `prompt` (string): Prompt to generate text from Evo2
- `temperature` (float): Temperature during sampling for generation
- `top_k` (integer): Top K during sampling for generation
- `top_p` (float): Top P during sampling for generation
- `max_new_tokens` (integer): Maximum number of tokens to generate
- `tensor_parallel_size` (integer): Order of tensor parallelism (default: 1)
- `pipeline_model_parallel_size` (integer): Order of pipeline parallelism (default: 1)
- `context_parallel_size` (integer): Order of context parallelism (default: 1)
- `output_file` (string): Output file path (optional, will use temp file if not provided)

**Example Request:**

```bash
curl -X POST http://localhost:5000/inference \
  -H "Content-Type: application/json" \
  -d '{
    "ckpt_dir": "/path/to/checkpoint",
    "prompt": ">d__Bacteria|p__Pseudomonadota|c__Gammaproteobacteria|o__Enterobacterales|f__Enterobacteriaceae|g__Escherichia|s__Escherichia_coli",
    "max_new_tokens": 1024,
    "temperature": 1.0
  }'
```

**Example Response:**

```json
{
  "success": true,
  "output": "Generated sequence text...",
  "stdout": "Command output...",
  "stderr": ""
}
```

### GET /checkpoints

Get all valid checkpoint directories available for inference.

**Example Request:**

```bash
curl http://localhost:5000/checkpoints
```

**Example Response:**

```json
{
  "checkpoints": [
    "/path/to/evo2/pretraining_demo/evo2/checkpoints/epoch=0-step=249-consumed_samples=16000.0",
    "/path/to/evo2/pretraining_demo/evo2/checkpoints/epoch=0-step=299-consumed_samples=19200.0",
    "/path/to/evo2/pretraining_demo/evo2/checkpoints/epoch=0-step=899-consumed_samples=57600.0-last"
  ],
  "count": 3
}
```

### GET /health

Health check endpoint.

**Example Request:**

```bash
curl http://localhost:5000/health
```

**Example Response:**

```json
{
  "status": "healthy"
}
```

## Error Handling

The API returns appropriate HTTP status codes:
- `200`: Success
- `400`: Bad request (missing required parameters)
- `500`: Internal server error (inference command failed)
- `504`: Gateway timeout (inference command timed out after 10 minutes)

Error responses include details in the JSON body:

```json
{
  "error": "Error message",
  "stderr": "Command stderr output",
  "stdout": "Command stdout output",
  "return_code": 1
}
```
