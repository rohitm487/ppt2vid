import requests
import time
import json
from pathlib import Path

def test_ppt_conversion():
    # API endpoint
    base_url = "http://localhost:8000"
    
    # File to upload
    ppt_file = Path("AI Agents.pptx")
    
    print(f"Uploading {ppt_file}...")
    
    # Upload the file
    with open(ppt_file, "rb") as f:
        response = requests.post(
            f"{base_url}/upload",
            files={"file": f}
        )
    
    if response.status_code != 200:
        print(f"Error uploading file: {response.text}")
        return
    
    # Get the processing ID from the response
    data = response.json()
    print(f"\nInitial status: {data['status']} - {data['message']}")
    
    # Extract processing ID from the response URL
    processing_id = response.headers.get('location', '').split('/')[-1]
    if not processing_id:
        print("Error: Could not get processing ID")
        return
    
    print(f"Processing ID: {processing_id}")
    
    # Monitor progress
    while True:
        status_response = requests.get(f"{base_url}/status/{processing_id}")
        if status_response.status_code != 200:
            print(f"\nError checking status: {status_response.text}")
            break
            
        status = status_response.json()
        progress = status.get('progress', 0) * 100
        print(f"\rStatus: {status['status']} - {status['message']} ({progress:.1f}%)", end="")
        
        if status["status"] == "completed":
            print("\nProcessing completed!")
            break
        elif status["status"] == "error":
            print(f"\nError: {status['message']}")
            break
        
        time.sleep(2)  # Wait 2 seconds before checking again
    
    # Get the results
    if status["status"] == "completed":
        result_response = requests.get(f"{base_url}/result/{processing_id}")
        if result_response.status_code != 200:
            print(f"\nError getting results: {result_response.text}")
            return
            
        result = result_response.json()
        
        # Save results to a file
        output_file = Path("presentation_results.json")
        with open(output_file, "w") as f:
            json.dump(result, f, indent=2)
        
        print(f"\nResults saved to {output_file}")

if __name__ == "__main__":
    test_ppt_conversion() 