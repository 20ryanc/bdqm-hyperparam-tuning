# SETUP<a name="setup"></a>

## Contents<a name="contents"></a>

<!-- mdformat-toc start --slug=github --maxlevel=6 --minlevel=1 -->

- [SETUP](#setup)
  - [Contents](#contents)
  - [Introduction](#introduction)
  - [Setup on PACE](#setup-on-pace)
  - [Setup on Generic System](#setup-on-generic-system)
  - [First Steps Running Hyperparameter Optimization Code](#first-steps-running-hyperparameter-optimization-code)

<!-- mdformat-toc end -->

## Introduction<a name="introduction"></a>

This document will take you through setting up your system to run parallel
GPU-accelerated hyperparameter optimization jobs with `ampopt`.

If you're on the PACE cluster, follow the instructions below ("Setup on PACE").
Otherwise, skip ahead to the section "Setup on Generic System".

## Setup on PACE<a name="setup-on-pace"></a>

1. Activate the Gatech VPN (https://docs.pace.gatech.edu/gettingStarted/vpn/)

1. Log in to the login node:

   ```bash
   ssh <your-gatech-username>@pace-ice.pace.gatech.edu
   ```

1. Clone repos:

   ```bash
   git clone https://github.com/ulissigroup/amptorch.git
   git clone https://github.com/20ryanc/bdqm-hyperparam-tuning.git
   ```

1. Start an interactive job:

   ```
   qsub ~/bdqm-hyperparam-tuning/jobs/interactive-gpu-session.pbs
   ```

   Note: all the following steps must happen inside the interactive job.

1. Activate the conda module:

   ```
   module load anaconda3/2021.05
   ```

1. Create the conda environment and install the project into it:

   ```
   conda env create -f ~/bdqm-hyperparam-tuning/env_gpu.yml
   conda activate bdqm-hpopt
   pip install -e ~/bdqm-hyperparam-tuning
   ```

1. Switch to the right amptorch branch and install it into the conda env:

   ```
   cd ~/amptorch
   git checkout BDQM_VIP_2022Feb
   pip install -e .
   ```

1. **MySQL setup for Remote Server**:

   1. ssh into remote server and foward port into local computer. In the example below port 3306 from the server is fowarded to port 5555 on the local machine. **Do Not Close**
      ```
      ssh <UserName>@<HostName> -L localhost:5555:localhost:3306
      ```
   1. Open a seperate terminal and ssh into PACE-ICE and reverse foward the local port into pace. The example fowards port 5555 from our local machine to PACE-ICE
      ```
      ssh -XC -A <UserName>@pace-ice.pace.gatech.edu -R localhost:5555:localhost:5555
      ```

1. Create a file `~/bdqm-hyperparam-tuning/.env` with the following contents:

   ```
   MYSQL_USERNAME=... # your sql username
   MYSQL_PASSWORD=... # your sql password
   HPOPT_DB=hpopt 
   MYSQL_HOSTNAME=... # 127.0.0.1 if you are doing port fowarding or running locally
   #Ignore rest if you are not using SSH Port Fowarding to connect to remote SSH server
   MYSQL_PORT=... # 5555 if you followed setup for remote server
   SSH_HOST=... # the hostname of ssh server
   SSH_USER=... # the username for ssh server
   SSH_PASS=... # password
   SSH_PORT=... # ssh port default is 22
   ```

## Setup on Generic System<a name="setup-on-generic-system"></a>

1. Clone repos:

   ```bash
   git clone https://github.com/ulissigroup/amptorch.git
   git clone https://github.com/20ryanc/bdqm-hyperparam-tuning.git
   ```

1. Ensure conda is installed

1. Change to the project directory:

   ```bash
   cd bdqm-hyperparam-tuning
   ```

1. Create the conda environment by running either `conda env create -f env_cpu.yml`
   or `conda env create -f env_gpu.yml` depending on if your system has a GPU
   available or not.

1. Install both packages locally into the conda environment:

   ```
   conda activate bdqm-hpopt
   pip install -e .
   cd ../amptorch
   pip install -e .
   ```

1. **Install MySQL**:

   1. Instructions vary depending on your platform, but on mac to install mysql
      you can just run `brew install mysql`.

   1. Start mysql by running `brew services start mysql` (again, this will
      be different for linux users).

   1. Choose a password and make a note of it

   1. Run this, **replacing 'my-secure-password' with the password you just chose**:

      ```
      mysqladmin -u root password 'my-secure-password'`
      ```

   1. Run `mysql -u root -p`. When prompted, enter your MySQL password.

   1. At the MySQL prompt, run `CREATE DATABASE hpopt;`

   1. Exit the MySQL prompt by running `exit`

1. Create a file `.env` in the `bdqm-hyperparam-tuning` folder with the
   following contents:

   ```
   MYSQL_USERNAME=root
   MYSQL_PASSWORD=... # the mysql password you set in step 8
   HPOPT_DB=hpopt
   MYSQL_HOSTNAME=localhost
   ```
