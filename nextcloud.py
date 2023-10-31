import pyrclone
import tempfile
import os

def create_rclone_config(nextcloud_url, nextcloud_user, nextcloud_pass):
    # Create a temporary rclone configuration file
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as config_file:
        config = f"""
            [nextcloud]
            type = webdav
            url = {nextcloud_url}
            vendor = nextcloud
            user = {nextcloud_user}
            pass = {nextcloud_pass}
            """
        config_file.write(config)
        return config_file.name

def sync_to_nextcloud(local_folder, remote_folder):

    # Get Nextcloud username and password from the .env file
    nc_username = os.environ['NEXTCLOUD_USER']
    nc_password = os.environ['NEXTCLOUD_PASS']
    nc_url = os.environ['NEXTCLOUD_URL']

    # Generate a temporary Rclone configuration file
    rclone_config_path = create_rclone_config(nc_url, nc_username, nc_password)

    try:
        # Set the RCLONE_CONFIG environment variable to the temporary config file
        os.environ["RCLONE_CONFIG"] = rclone_config_path

        # Initialize a connection to Rclone
        rclone = pyrclone.Rclone()

        # Synchronize the local folder with the remote folder
        result = rclone.sync(local_folder, f"nextcloud:{remote_folder}")
        print(result)

    finally:
        # Delete the temporary configuration file
        if os.path.exists(rclone_config_path):
            os.remove(rclone_config_path)

# Example usage
local_folder = "markdown_files"
remote_folder = ".Notes/Current"

sync_to_nextcloud(local_folder, remote_folder)

