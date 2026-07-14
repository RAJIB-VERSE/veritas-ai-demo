"""
Export the trained Hugging Face model to the Hugging Face Hub.
Requires: pip install huggingface_hub
"""

import os
import argparse

try:
    from huggingface_hub import HfApi, create_repo
except ImportError:
    print("Missing dependency. Run: pip install huggingface_hub")
    import sys
    sys.exit(1)


def push_to_hub(model_dir, repo_id, token):
    if not os.path.exists(model_dir):
        print(f"Error: Model directory {model_dir} not found.")
        return
        
    api = HfApi()
    
    print(f"Creating repo {repo_id} if it doesn't exist...")
    try:
        create_repo(repo_id, token=token, exist_ok=True, private=False)
    except Exception as e:
        print(f"Repo creation error (might already exist): {e}")
        
    print(f"Uploading model files from {model_dir} to {repo_id}...")
    try:
        api.upload_folder(
            folder_path=model_dir,
            repo_id=repo_id,
            repo_type="model",
            token=token,
            commit_message="Upload fine-tuned fake news detection model"
        )
        print("Upload complete!")
        print(f"Your model is now available at: https://huggingface.co/{repo_id}")
    except Exception as e:
        print(f"Upload failed: {e}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Push model to Hugging Face Hub")
    parser.add_argument('--model_dir', type=str, default='saved_models/distilbert_fakenews')
    parser.add_argument('--repo_id', type=str, required=True, help="e.g., your-username/fakenews-distilbert")
    parser.add_argument('--token', type=str, help="HF Token (or set HF_TOKEN env var)")
    args = parser.parse_args()
    
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    model_dir = os.path.join(base_dir, args.model_dir)
    
    token = args.token or os.environ.get('HF_TOKEN')
    if not token:
        print("Error: Hugging Face token required. Pass via --token or HF_TOKEN env var.")
        import sys
        sys.exit(1)
        
    push_to_hub(model_dir, args.repo_id, token)
