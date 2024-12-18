import base64
import requests

def upload_images_via_paths(paths, base_url):

    base64_images = []

    for path in paths:
        try:
            with open(path, "rb") as image_file:
                encoded = base64.b64encode(image_file.read()).decode("utf-8")
                base64_images.append(encoded)
        except FileNotFoundError:
            print(f"File not found: {path}")
        except Exception as e:
            print(f"Error encoding image at {path}: {e}")
    
    if not base64_images:
        print("No valid images found to upload.")
        return {"error": "No images uploaded"}

    payload = {"base64_images": base64_images}
    try:
        response = requests.post(f"{base_url}/upload_images", json=payload)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return {"error ": str(e)}
    
if __name__ == "__main__":
    image_paths = [r"C:\Users\setya\Documents\Code\SnapSort\ML\guest3.jpg", r"C:\Users\setya\Documents\Code\SnapSort\ML\guestar2.jpg", r"C:\Users\setya\Documents\Code\SnapSort\ML\guestl1.jpg"]
    fastapi_base_url = "http://127.0.0.1:8000"

    result = upload_images_via_paths(image_paths,fastapi_base_url)
    print(result)
    payload = {
        "local_directory":"queue",
        "similarity_threshold":0.35 
    }

    url="http://127.0.0.1:8000/match_faces"

    try:
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            print("Match Faces Response:")
            print(response.json())
        else:
            print(f"Failed to call match_faces. Status Code: {response.status_code}")
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"An error occurred: {e}")

