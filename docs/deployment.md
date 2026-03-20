Instructions to deploy this application to GCP Google Compute Engine VM using Docker compose.
Images are stored in artifact registry.

Step 0: 
Make sure Docker Desktop is running.


Step 1: Spin up VM (if does not exist)
In GCP, navigate to Compute Engine tab. Go to Compute Engine -> VM Instances
Create Instance. Choose N1 machine type if available, next cheapest otherwise. In security tab, allow full access to all cloud APIs.


Step 2: Build and push docker images.
Make sure the API endpoint in App.tsx, line 247, is using the external IP of our vm. Can be found under Network Interfaces in the VM menu. This IP is ephemeral, will change whenever you reboot the vm.

Here are the commands to build and push the docker images:

docker build -t {artifact registry region}-docker.pkg.dev/{project id}/{artifact registry name}/{frontend/backend}:latest -f Dockerfile .
docker push {artifact registry region}-docker.pkg.dev/{project id}/{artifact registry name}/{frontend/backend}:latest

Here is an example with values filled in:

Navigate to frontend and run the following in the terminal:
docker build -t us-east1-docker.pkg.dev/rpg-map-generator/rpg-map-generator-repository/frontend:latest -f Dockerfile .
docker push us-east1-docker.pkg.dev/rpg-map-generator/rpg-map-generator-repository/frontend:latest

Navigate to backend and run the following:
docker build -t us-east1-docker.pkg.dev/rpg-map-generator/rpg-map-generator-repository/backend:latest -f Dockerfile .
docker push us-east1-docker.pkg.dev/rpg-map-generator/rpg-map-generator-repository/backend:latest


Step 3: Set up VM via SSH
In GCP, navigate to VM and click on drop down for SSH button, choose "View gcloud command", copy the command.
In your terminal, paste the command. It should look something like this:
gcloud compute ssh --zone "us-east1-c" "rpg-map-generator-vm" --project "rpg-map-generator"

Run the following commands to set up Docker on the VM:
sudo apt-get install docker
sudo apt-get install docker-compose
gcloud auth configure-docker us-east1-docker.pkg.dev

Run the following commands to set up firewall:
gcloud compute firewall-rules create allow-port-8000 --allow tcp:8000 --source-ranges 0.0.0.0/0
gcloud compute firewall-rules create allow-port-5173 --allow tcp:5173 --source-ranges 0.0.0.0/0

In root, create a file called docker-compose.yml. Paste the contents of docker-compose-example-vm.yml into it.

Run the following commands: 
docker-compose pull
docker-compose up -d

