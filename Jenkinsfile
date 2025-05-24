// Jenkinsfile
pipeline {
    agent any // Or 'agent { label 'your-jenkins-agent-label' }' if you have specific agents

    environment {
        // --- Render Specific Variables ---
        // Find your Render Service ID in the Render dashboard URL for the service
        // Example URL: https://dashboard.render.com/web/srv-xxxxxxxxxxxxxxxxxxxx/settings
        // The ID is 'srv-xxxxxxxxxxxxxxxxxxxx'
        RENDER_DEV_SERVICE_ID = 'srv-d0h686q4d50c73c6g410'
        RENDER_PROD_SERVICE_ID = 'YOUR_RENDER_PROD_SERVICE_ID' // Only needed if you implement production deploy

        // Jenkins Credential ID for your Render API Key (Secret Text credential)
        // Go to Manage Jenkins -> Manage Credentials -> Jenkins -> Global credentials (unrestricted)
        // Add a 'Secret text' credential with your Render API Key
        RENDER_API_KEY = credentials('your-render-api-key-credential-id')

        // URL of your Render Dev service (e.g., https://my-app-dev.onrender.com)
        DEV_APP_URL = 'https://my-app-dev.onrender.com'

        // --- GitHub Specific Variables ---
        // Jenkins Credential ID for your GitHub repository (e.g., Username with password or Secret text for PAT)
        GITHUB_CREDENTIAL_ID = 'your-github-credential-id'
        GITHUB_REPO_URL = 'https://github.com/your-username/your-repo.git'

        // --- Python/Test Specific Variables ---
        PYTHON_VERSION = '3.10' // Match your application's/test's Python version
        // This is passed to your tests. Ensure your conftest.py or test code can read it.
        #BASE_URL_FOR_TESTS = DEV_APP_URL // You can use this if you want to pass it as an env var to tests
    }

    stages {
        stage('Checkout Source') {
            steps {
                echo "Checking out source code from ${GITHUB_REPO_URL} branch dev"
                git branch: 'dev', credentialsId: GITHUB_CREDENTIAL_ID, url: GITHUB_REPO_URL
            }
        }

        stage('Trigger Render Dev Deployment') {
            steps {
                echo "Triggering new deployment for Render Dev service: ${RENDER_DEV_SERVICE_ID}"
                // This command sends a POST request to Render's API to trigger a new deploy.
                // Render will then automatically pull the latest code from the 'dev' branch (as configured earlier).
                sh "curl -X POST -H \"Authorization: Bearer ${RENDER_API_KEY}\" https://api.render.com/v1/services/${RENDER_DEV_SERVICE_ID}/deploys"
                echo "Deployment triggered on Render Dev service. Waiting for Render to start build..."
                sleep 20 // Give Render a moment to acknowledge the deploy trigger
            }
        }

        stage('Wait for Render Dev App to be Responsive') {
            steps {
                script {
                    def maxRetries = 30 // Max number of checks
                    def retryInterval = 20 // seconds between retries
                    def deployed = false

                    echo "Waiting for Render Dev app at ${DEV_APP_URL} to become responsive..."
                    timeout(time: maxRetries * retryInterval, unit: 'SECONDS') { // Total timeout for this stage
                        for (int i = 0; i < maxRetries; i++) {
                            try {
                                // Attempt to hit a specific, expected endpoint (e.g., the login page)
                                // '--fail' makes curl return a non-zero exit code on HTTP errors (4xx/5xx)
                                // '--silent' suppresses curl output
                                // '--output /dev/null' discards response body
                                // '--head' retrieves only HTTP headers
                                sh "curl --fail --silent --output /dev/null --head --request GET ${DEV_APP_URL}/login"
                                echo "Render Dev app is responsive!"
                                deployed = true
                                break // Exit loop if successful
                            } catch (e) {
                                echo "Attempt ${i + 1}/${maxRetries}: Render Dev app not yet responsive. Retrying in ${retryInterval} seconds..."
                                sleep retryInterval
                            }
                        }
                    }
                    if (!deployed) {
                        error("Render Dev deployment failed to become responsive within timeout. Tests cannot proceed.")
                    }
                }
            }
        }

        stage('Setup Test Environment and Run Selenium Tests') {
            steps {
                script {
                    echo "Setting up Python environment and installing dependencies..."
                    // Create and activate virtual environment
                    sh "python${PYTHON_VERSION} -m venv venv"
                    sh "source venv/bin/activate"

                    // Install Python dependencies for your tests
                    // Assuming you have a requirements.txt in your repo for your test environment
                    sh "pip install -r requirements.txt"
                    // Ensure core Selenium/Pytest dependencies are also installed if not in requirements.txt
                    sh "pip install selenium pytest webdriver-manager"

                    echo "Running Selenium tests against ${DEV_APP_URL}..."
                    // Run your Pytest tests.
                    // IMPORTANT: Your conftest.py (or test code) must be set up to accept the --base-url option
                    // and use it to configure the driver's base URL.
                    sh "pytest --base-url ${DEV_APP_URL} --browser chrome src/tests/"

                    // If your tests use an environment variable for BASE_URL instead of a --base-url option:
                    // withEnv(['BASE_URL=' + DEV_APP_URL]) {
                    //     sh "pytest --browser chrome src/tests/"
                    // }
                }
            }
        }

        stage('Conditional Deploy to Render Production') {
            when {
                // This stage only runs if the previous stage (Selenium Tests) was successful
                expression { currentBuild.currentResult == 'SUCCESS' }
            }
            steps {
                echo "Tests passed! Proceeding to deploy to Production."
                // This curl command assumes you have a separate Render service for production
                // that you deploys from your 'main' (or 'master') branch.
                sh "curl -X POST -H \"Authorization: Bearer ${RENDER_API_KEY}\" https://api.render.com/v1/services/${RENDER_PROD_SERVICE_ID}/deploys"
                echo "Triggered deployment on Render Production service."
            }
        }
    }

    post {
        always {
            echo "Pipeline finished. Status: ${currentBuild.currentResult}"
        }
        failure {
            echo "Pipeline failed. Production deployment skipped."
            // You can add notification steps here (e.g., email, Slack, Teams)
            // Example: mail to: 'your-email@example.com', subject: "CI/CD Pipeline Failed: ${env.JOB_NAME}", body: "Build ${env.BUILD_NUMBER} failed. Check console output: ${env.BUILD_URL}"
        }
        success {
            echo "Pipeline succeeded. Application deployed to production if configured."
            // Optional: Send success notifications
        }
    }
}