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
        #response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return {"error ": str(e)}
    
if __name__ == "__main__":
    image_paths = [r"C:\Users\setya\Documents\Code\SnapSort\ML\guest3.jpg", r"C:\Users\setya\Documents\Code\SnapSort\ML\guestar2.jpg", r"C:\Users\setya\Documents\Code\SnapSort\ML\guestl1.jpg"]
    fastapi_base_url = "http://127.0.0.1:8000"
    result = upload_images_via_paths(image_paths,fastapi_base_url)
    print(result)
