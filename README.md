# docker-registry-purge

=> work with registry v1

With the docker registry image when you delete an image with the API, data is not deleted (there is no garbage collection).

=> This script delete it for you.
So now, when you delete an image with the Docker registry API, you can launch this script, and it will clean your disk.
