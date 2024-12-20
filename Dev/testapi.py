import base64
import requests
import os
import matplotlib.pyplot as plt
from PIL import Image

def display_matches(matches):
    current_directory = os.getcwd()  # Get the current working directory
    for match_id, image_paths in matches.items():
        print(f"Match ID: {match_id}")
        
        # Create a subplot for the current match
        num_images = len(image_paths)
        cols = 3  # Number of columns in the grid
        rows = (num_images + cols - 1) // cols  # Calculate rows needed

        fig, axes = plt.subplots(rows, cols, figsize=(15, 5 * rows))
        axes = axes.flatten()  # Flatten to access axes in a 1D array

        for i, image_path in enumerate(image_paths):
            try:
                # Construct the full path to the image
                full_path = os.path.join(current_directory, image_path)
                print(f"Attempting to open: {full_path}")

                # Open and display the image
                img = Image.open(full_path)
                axes[i].imshow(img)
                axes[i].set_title(os.path.basename(full_path))  # Display the file name as the title
                axes[i].axis("off")
            except FileNotFoundError:
                print(f"File not found: {full_path}")
                axes[i].axis("off")
            except Exception as e:
                print(f"Error loading image {full_path}: {e}")
                axes[i].axis("off")

        # Hide any extra axes if the grid is larger than the number of images
        for j in range(len(image_paths), len(axes)):
            axes[j].axis("off")

        plt.tight_layout()
        plt.show()
        break

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
    payload = {
        "local_directory":"queue",
        "similarity_threshold":0.35
    }

    url="http://127.0.0.1:8000/match_faces"

    try:
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            print("Match Faces Response:")
            display_matches(response.json()['matches'])
            print(response.json())
        else:
            print(f"Failed to call match_faces. Status Code: {response.status_code}")
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"An error occurred: {e}")

