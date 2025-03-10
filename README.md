# Docker Desktop direct download links

> Track and list all Docker Desktop direct download links since version `4.0.0` (released on `2021-08-31`).

All **Docker Desktop** resources with versions later than **`4.0.0`** are listed in the [**Docker Desktop** release notes page](https://docs.docker.com/desktop/release-notes).
Earlier versions are no longer available for download.

**All the links to the different versions of Docker Desktop are referenced in the [DockerDesktop.yaml](DockerDesktop.yaml) file.**

The direct download links are all composed as follows:
```
https://desktop.docker.com/<OS>/main/<ARCHITECTURE>/<GUID>/<FILE>
```
* **OS** can be `win`, `mac` or `linux`.
* **ARCHITECTURE** can be `amd64` or `arm64`.
* **GUID** is linked to the version.
* **FILE** is linked to the **OS** and **ARCHITECTURE**
    * `Docker Desktop Installer.exe` for **Windows**
    * `Docker.dmg` for **Mac**
    * `docker-desktop-amd64.deb` for **Debian Linux** (only `amd64`)
    * `docker-desktop-x86_64.rpm` for **RPM Linux** (only `amd64`)
    * `docker-desktop-x86_64.pkg.tar.zst` for **Arch Linux** (only `amd64`)

Download links are not referenced for some resources, even if the links still exist.
The [`docker_release_scraper.py`](docker_release_scraper.py) script is used to list all the direct download links for all the different **Docker Desktop** resources and provide a method to keep them up to date.

Thanks [@kupietools](https://gist.github.com/kupietools) for his [previous work](https://gist.github.com/kupietools/2f9f085228d765da579f0f0702bec33c).
