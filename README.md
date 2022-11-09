Clone the repository "configuration-driven-cicd-pipeline" to your local machine

Change current working directory to the repo directory once cloned
```
cd configuration-driven-cicd-pipeline
```

Manually create a virtualenv:
```
$ python3 -m venv .venv
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

For MacOS and Linux:
```
$ source .venv/bin/activate
```

For Windows:
```
% .venv\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```
$ pip install -r requirements.txt
```

Configure the profile of the account in your terminal

```
export AWS_PROFILE=<profile-name>
```

At this point you can now synthesize the CloudFormation template for this code

```
$ cdk synth
```

Create a CodeCommit repository in the account you want to deploy this pipeline with the name "BlogInfrastructure".

Add this repository as remote to your cloned repository
```
git remote add <remote-name> <code-commit-repo-url>
```

The cloned repository contains 2 folders:
1. sample-application-repo - Will be used to deploy a sample application using CodePipeline
2. automated-tests-repo - Will be used to run automated tests after application deployment

Move these 2 repos out of the configuration-driven-cicd-pipeline cloned repo to another location on your local machine

Push the code to "BlogInfrastructure" repository in branch main
```
git push <remote-name> main
```

Perform following steps to push sample-application-repo to CodeCommit
```
Create a CodeCommit repo with the name 'sample-application-repo' in the same AWS account.

1. Change directory to sample-application-repo on your local 
    cd sample-application-repo
2. git init
3. git add .
4. git commit -m "sample application code initial commit"
5. git remote add origin <sample-application-repo-url>
6. git push -u origin main

```
Perform following steps to push automated-tests-repo to CodeCommit
```
Create a CodeCommit repo with the name 'automated-tests-repo' in the same AWS account.

1. Change directory to sample-application-repo on your local 
    cd sample-application-repo
2. git init
3. git add .
4. git commit -m "automated test code initial commit"
5. git remote add origin <automated-tests-repo-url>
6. git push -u origin main

```


Navigate back to configuration-driven-cicd-pipeline on your local and run the following command to deploy the stack
```
cdk deploy
```

This will create the required infrastructure and CodePipeline for the CDK app.