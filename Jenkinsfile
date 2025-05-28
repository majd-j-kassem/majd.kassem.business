pipeline {
    agent any // This means the entire pipeline runs on any available Jenkins agent.

    environment {
        SUT_REPO = 'https://github.com/majd-j-kassem/majd.kassem.business.git'
        QA_REPO = 'https://github.com/majd-j-kassem/majd.kassem.business_qa.git'
        SUT_BRANCH_DEV = 'dev'
        SUT_BRANCH_MAIN = 'main'
        QA_BRANCH = 'dev' // Make sure this matches your QA repo branch name
        STAGING_URL = 'https://majd-kassem-business-dev.onrender.com/'
        LIVE_URL = 'https://majd-kassem-business.onrender.com/'
        // Define the name for your custom QA test runner Docker image
        QA_TEST_RUNNER_IMAGE = 'my-qa-test-runner:latest'
    }

    stages {
        stage('Checkout SUT Dev') {
            steps {
                git branch: env.SUT_BRANCH_DEV, credentialsId: 'git_id', url: env.SUT_REPO
            }
        }

        stage('Build and Deploy SUT to Staging') {
            steps {
                script {
                    echo "SUT automatically deployed to staging by Render on commit to ${env.SUT_BRANCH_DEV}"
                    // Wait for Render to finish deploying. You might adjust this based on Render's typical deployment time.
                    sleep 30
                }
            }
        }

        stage('Checkout QA Main') {
            steps {
                dir('qa-project') {
                    git branch: env.QA_BRANCH, credentialsId: 'git_id', url: env.QA_REPO
                }
            }
        }

        // --- NEW STAGE: Build the custom QA Docker Image ---
        stage('Build QA Runner Image') {
            // This stage runs on the main Jenkins agent (your jenkins-server container)
            // which has access to the Docker daemon on the host via the mounted socket.
            agent any
            steps {
                script {
                    // Navigate to the directory containing your Dockerfile
                    // Assuming Dockerfile is in a 'qa-project' subfolder within your SUT_REPO (main repo)
                    dir('qa-project') {
                        echo "Building Docker image: ${env.QA_TEST_RUNNER_IMAGE}"
                        // Build the image using the Dockerfile from qa-project/Dockerfile
                        // The '.' means build context is the current directory (qa-project)
                        sh "docker build -t ${env.QA_TEST_RUNNER_IMAGE} ."
                    }
                }
            }
        }

        stage('Run QA Tests against Staging') {
            agent {
                // Use the custom image that now includes Docker CLI
                docker {
                    image env.QA_TEST_RUNNER_IMAGE
                    // CRITICAL: Mount the host's Docker socket into this QA runner container
                    // This allows the Docker client *inside* this QA container to talk to the *host's* Docker daemon
                    args "-v /var/run/docker.sock:/var/run/docker.sock -u root" // Keep -u root for now, or ensure seluser can use docker
                }
            }
            steps {
                // Ensure commands run from the correct directory within the agent container
                // The custom Dockerfile sets WORKDIR /app and copies project files there.
                // So, adjust paths relative to /app.
                script {
                    echo "Running QA tests using Docker image: ${env.QA_TEST_RUNNER_IMAGE}"
                    // Check if docker command is available
                    sh "which docker"
                    sh "docker --version"
                    // Test Docker connection
                    sh "docker ps -a"

                    // Install Python requirements (if not already installed in the image)
                    // If you added `COPY requirements.txt .` and `RUN pip install` in your Dockerfile,
                    // these lines might be redundant unless you want to re-install.
                    // Assuming `requirements.txt` is at `/app/requirements.txt` in the container.
                    sh '/opt/venv/bin/pip install --no-cache-dir -r requirements.txt'

                    // Your pytest command. Ensure your QA project has 'pytest' installed via requirements.txt.
                    // Assuming your tests are in '/app/src/tests' within the container.
                    sh "pytest src/tests --browser chrome-headless --base-url ${env.STAGING_URL}"
                }
            }
        }

        stage('Update SUT Main and Deploy to Live') {
            when {
                expression { currentBuild.result == 'SUCCESS' }
            }
            steps {
                script {
                    // Checkout SUT repo again to ensure we're on the correct state for merging.
                    // This 'git_id' should be the same as used in other git steps.
                    dir('sut-main-repo') { // Create a separate directory to avoid conflicts with 'qa-project'
                        git branch: env.SUT_BRANCH_MAIN, credentialsId: 'git_id', url: env.SUT_REPO
                        sh "git config user.email 'jenkins@example.com'"
                        sh "git config user.name 'Jenkins'"
                        sh "git merge ${env.SUT_BRANCH_DEV} -m 'Merge dev to main after successful QA tests'"
                        sh "git push origin ${env.SUT_BRANCH_MAIN}"
                        echo "SUT Main branch updated and deployed to live by Render."
                    }
                }
            }
        }
    }

    post {
        failure {
            echo 'Pipeline failed. No deployment to live.'
        }
        success {
            echo 'Pipeline succeeded. Live deployment triggered.'
        }
    }
}