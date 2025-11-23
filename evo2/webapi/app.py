from flask import Flask, request, jsonify
import subprocess
import os
import tempfile
import uuid
import re
import logging

# Set environment variables to help with GPU detection
os.environ['CUDA_VISIBLE_DEVICES'] = os.environ.get('CUDA_VISIBLE_DEVICES', '0')
os.environ['NVIDIA_DISABLE_REQUIRE'] = '1'

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/inference', methods=['POST'])
def inference():
    """
    Endpoint to run Evo2 inference.
    
    Required parameters:
    - ckpt_dir: Path to checkpoint directory containing pre-trained Evo2 model
    
    Optional parameters:
    - prompt: Prompt to generate text from Evo2
    - temperature: Temperature during sampling for generation
    - top_k: Top K during sampling for generation
    - top_p: Top P during sampling for generation
    - max_new_tokens: Maximum number of tokens to generate
    - tensor_parallel_size: Order of tensor parallelism (default: 1)
    - pipeline_model_parallel_size: Order of pipeline parallelism (default: 1)
    - context_parallel_size: Order of context parallelism (default: 1)
    - output_file: Output file path (optional, will use temp file if not provided)
    """
    try:
        data = request.get_json()
        
        # Validate required parameters
        if not data or 'ckpt_dir' not in data:
            return jsonify({
                'error': 'Missing required parameter: ckpt_dir'
            }), 400
        
        # Build command
        cmd = ['infer_evo2', '--ckpt-dir', data['ckpt_dir']]
        
        # Add optional parameters
        if 'prompt' in data:
            cmd.extend(['--prompt', str(data['prompt'])])
        
        if 'temperature' in data:
            cmd.extend(['--temperature', str(data['temperature'])])
        
        if 'top_k' in data:
            cmd.extend(['--top-k', str(data['top_k'])])
        
        if 'top_p' in data:
            cmd.extend(['--top-p', str(data['top_p'])])
        
        if 'max_new_tokens' in data:
            cmd.extend(['--max-new-tokens', str(data['max_new_tokens'])])
        
        if 'tensor_parallel_size' in data:
            cmd.extend(['--tensor-parallel-size', str(data['tensor_parallel_size'])])
        
        if 'pipeline_model_parallel_size' in data:
            cmd.extend(['--pipeline-model-parallel-size', str(data['pipeline_model_parallel_size'])])
        
        if 'context_parallel_size' in data:
            cmd.extend(['--context-parallel-size', str(data['context_parallel_size'])])
        
        # Handle output file
        output_file = data.get('output_file')
        use_temp_file = output_file is None
        
        if use_temp_file:
            # Create a temporary file for output
            temp_file = tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.txt')
            output_file = temp_file.name
            temp_file.close()
        
        cmd.extend(['--output-file', output_file])
        
        # Prepare environment for subprocess with GPU settings
        env = os.environ.copy()
        env['CUDA_VISIBLE_DEVICES'] = env.get('CUDA_VISIBLE_DEVICES', '0')
        env['NVIDIA_DISABLE_REQUIRE'] = '1'
        
        # Execute the command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,  # 10 minute timeout
            env=env
        )
        
        # Log the full output
        logger.info("=== Command executed ===")
        logger.info(f"Command: {' '.join(cmd)}")
        logger.info(f"Return code: {result.returncode}")
        logger.info(f"=== STDOUT ===\n{result.stdout}")
        logger.info(f"=== STDERR ===\n{result.stderr}")
        
        # Check if command was successful
        if result.returncode != 0:
            return jsonify({
                'error': 'Inference command failed',
                'return_code': result.returncode
            }), 500
        
        # Parse the generated text from the output
        generated_text = None
        inference_time = None
        tokens_per_sec = None
        
        # Combine stdout and stderr since the output can be in either
        full_output = result.stdout + "\n" + result.stderr
        
        # Extract generated_text using regex
        match = re.search(r"generated_text='([^']*)'", full_output)
        if match:
            generated_text = match.group(1)
        
        # Extract inference time and token rate
        time_match = re.search(r"Inference time:\s+([\d.]+)\s+seconds,\s+([\d.]+)\s+tokens/sec", full_output)
        if time_match:
            inference_time = float(time_match.group(1))
            tokens_per_sec = float(time_match.group(2))
        
        # Read output file if it exists (as backup)
        if not generated_text and os.path.exists(output_file):
            with open(output_file, 'r') as f:
                generated_text = f.read()
        
        # Clean up temp file if used
        if use_temp_file and os.path.exists(output_file):
            os.unlink(output_file)
        
        return jsonify({
            'success': True,
            'generated_text': generated_text,
            'inference_time_seconds': inference_time,
            'tokens_per_second': tokens_per_sec,
            'generated_length': len(generated_text) if generated_text else 0
        }), 200
        
    except subprocess.TimeoutExpired:
        return jsonify({
            'error': 'Inference command timed out'
        }), 504
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500


@app.route('/checkpoints', methods=['GET'])
def get_checkpoints():
    """
    Get all valid checkpoint directories.
    Returns a list of subdirectories in evo2/pretraining_demo/evo2/checkpoints/
    """
    try:
        # Get the base directory (two levels up from webapi)
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        checkpoints_dir = os.path.join(base_dir, 'pretraining_demo', 'evo2', 'checkpoints')
        
        if not os.path.exists(checkpoints_dir):
            return jsonify({
                'error': f'Checkpoints directory not found: {checkpoints_dir}'
            }), 404
        
        # Get all subdirectories
        checkpoints = [
            os.path.join(checkpoints_dir, d)
            for d in os.listdir(checkpoints_dir)
            if os.path.isdir(os.path.join(checkpoints_dir, d))
        ]
        
        return jsonify({
            'checkpoints': checkpoints,
            'count': len(checkpoints)
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'healthy'}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
