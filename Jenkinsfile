// Jenkinsfile for the System Under Test (SUT) repository:
// majd.kassem.business.git
// This file assumes your SUT is a Python application.

pipeline {
    // Defines the Jenkins agent/node where the pipeline will run.
    // 'any' means Jenkins can use any available agent.
    agent any

    // IMPORTANT: No 'tools { maven 'M3' }' directive here, as this is a Python SUT.

    // Environment variables accessible throughout the pipeline.
    // These should be configured as 'Secret text' credentials in Jenkins if sensitive.
    environment {
        // --- Render Service URLs ---
        RENDER_DEV_URL = 'https://majd-kassem-business-dev.onrender.com/'
        RENDER_PROD_URL = 'https://majd-kassem-business.onrender.com/'

        // --- IMPORTANT: Render Service IDs ---
        // Get these from your Render Dashboard URL for each service (e.g., srv-xxxxxxxxxxxxxxxxx).
        // These are used for triggering deployments via the Render API.
        RENDER_DEV_SERVICE_ID = 'srv-your-dev-service-id' // <<< IMPORTANT: Replace with your actual Render Dev Service ID!
        RENDER_LIVE_SERVICE_ID = 'srv-d0h686q4d50c73c6g410' // Your existing Render Live Service ID.

        // --- IMPORTANT: Jenkins Credential ID for Render API Key ---
        // This MUST match the ID you gave your Secret text credential in Jenkins.
        RENDER_API_KEY_CREDENTIAL_ID = 'render-api-key' // <<< IMPORTANT: Ensure this matches your Jenkins credential ID!
    }

    // Triggers define how the pipeline is started.
    triggers {
        // Poll SCM every 2 minutes for changes in this SUT repository.
        pollSCM('H/2 * * * *')
    }

    // Stages define the sequential steps of your pipeline.
    stages {
        // The 'Declarative: Checkout SCM' stage implicitly runs at the very beginning of the pipeline
        // because 'agent any' is at the top level and the Jenkins job is configured to use 'Pipeline script from SCM'.
        // It automatically checks out the SUT repository (majd.kassem.business.git) into the workspace root.

        // Stage to "build" your System Under Test (SUT) (Python).
        // For many Python web apps deployed with Render, the 'build' step in Jenkins
        // might be minimal as Render handles dependency installation (requirements.txt)
        // and starting the app. This stage can be used for things like linting,
        // running Python unit tests (if any), or other pre-deployment checks.
        stage('Build SUT (Python)') {
            steps {
                script {
                    echo "Building the System Under Test (SUT) (Python)..."
                    // If your Python SUT has unit tests or linters you want to run here, add them.
                    // Example: Run Python unit tests (assuming 'pytest' is installed via a virtual env or globally on agent)
                    // sh 'python -m pip install -r requirements.txt' // Usually not needed in Jenkins if Render handles
                    // sh 'pytest' // Example: Run Python unit tests if your SUT has them

                    // If your Python SUT is just a collection of files Render will deploy,
                    // and it doesn't have local build steps or tests at this stage,
                    // this stage might just be an echo, which is perfectly fine.
                    echo "Python SUT build/preparation complete. (Render will handle dependencies)."
                }
            }
            // Post-actions for this specific stage.
            post {
                failure {
                    error "SUT Build (Python) Failed! Cannot proceed with deployment. ❌"
                }
            }
        }

        // Stage to deploy the built SUT to the Render Dev Service using the Render API.
        stage('Deploy to Dev Service') {
            steps {
                script {
                    echo "Triggering deployment of SUT to Render Dev Service: ${env.RENDER_DEV_URL}"
                    // 'withCredentials' securely injects the Render API Key from Jenkins credentials store.
                    withCredentials([string(credentialsId: env.RENDER_API_KEY_CREDENTIAL_ID, variable: 'RENDER_API_KEY')]) {
                        // Using Render API to trigger a deploy.
                        sh "curl -X POST -H \"Authorization: Bearer ${RENDER_API_KEY}\" \"https://api.render.com/v1/services/${env.RENDER_DEV_SERVICE_ID}/deploys\""
                    }
                    echo "Deployment trigger sent to Render Dev! Check Render dashboard for status."
                    echo "Waiting a few seconds for Render to initiate deployment..."
                    sleep 10 // Give Render a moment to start the deploy.
                }
            }
            // Post-actions for this specific stage.
            post {
                failure {
                    error "Failed to trigger Render Dev deployment! Please check API key, Service ID, or Render status. ❌"
                }
                success {
                    echo "Successfully triggered Render Dev deployment. 🎉"
                }
            }
        }

        // Stage to trigger the separate QA-Selenium-Pipeline job.
        // This job will then perform the actual UI tests against the deployed Dev service.
        stage('Trigger QA Tests') {
            steps {
                script {
                    echo "Triggering QA-Selenium-Pipeline job..."
                    // The 'build' step triggers another Jenkins job by its name.
                    // 'parameters' allows passing dynamic data to the triggered job.
                    // 'wait: true' ensures this pipeline pauses until the QA job completes (or fails).
                    build job: 'QA-Selenium-Pipeline',
                          parameters: [
                              string(name: 'SUT_DEV_URL', value: env.RENDER_DEV_URL), // Pass the Dev URL as a parameter.
                              string(name: 'SUT_BUILD_NUMBER', value: env.BUILD_NUMBER) // Pass the current SUT build number for traceability.
                          ],
                          wait: true // Wait for the QA job to complete before proceeding (useful for overall pipeline status).
                    echo "QA-Selenium-Pipeline job triggered and completed (or failed)."
                }
            }
            // Post-actions for this specific stage.
            post {
                failure {
                    // If the QA job fails, this pipeline will also be marked as failure.
                    error "QA-Selenium-Pipeline job FAILED! Check its console output for details. ❌"
                }
                success {
                    echo "QA-Selenium-Pipeline job completed successfully. ✅"
                }
                unstable {
                    echo "QA-Selenium-Pipeline job completed with UNSTABLE result (e.g., some tests failed but not all). ⚠️"
                    // You might choose to still proceed to Live deploy if UNSTABLE is acceptable.
                }
            }
        }

        // Stage to deploy to Render Live, but ONLY if QA tests passed.
        stage('Deploy to Live Service') {
            when {
                // This 'when' condition ensures this stage only runs if the previous stages (especially QA Tests)
                // completed successfully. For an 'unstable' QA test result, you might adjust 'SUCCESS' to 'UNSTABLE'
                // or check for 'currentBuild.currentResult == "SUCCESS" || currentBuild.currentResult == "UNSTABLE"'
                // depending on your desired promotion policy.
                expression {
                    return currentBuild.currentResult == 'SUCCESS' // Only deploy to Live if all previous stages succeeded
                }
            }
            steps {
                script {
                    echo "QA Tests passed. Triggering deployment of SUT to Render Live Service: ${env.RENDER_PROD_URL}"
                    withCredentials([string(credentialsId: env.RENDER_API_KEY_CREDENTIAL_ID, variable: 'RENDER_API_KEY')]) {
                        sh "curl -X POST -H \"Authorization: Bearer ${RENDER_API_KEY}\" \"https://api.render.com/v1/services/${env.RENDER_LIVE_SERVICE_ID}/deploys\""
                    }
                    echo "Deployment trigger sent to Render Live! Check Render dashboard for status."
                }
            }
            post {
                failure {
                    error "Failed to trigger Render Live deployment! Please check API key, Service ID, or Render status. ❌"
                }
                success {
                    echo "Successfully triggered Render Live deployment. 🎉"
                }
            }
        }
    }

    // Global post-actions that run after the entire pipeline has finished, regardless of overall status.
    post {
        always {
            echo "Pipeline finished for job ${env.JOB_NAME}, build number ${env.BUILD_NUMBER}."
        }
        success {
            echo "Overall SUT-Dev-Pipeline SUCCESS: Build, Dev deploy, QA tests, and Live deploy all passed. 🎉"
        }
        failure {
            echo "Overall SUT-Dev-Pipeline FAILED: Check above stages for errors. ❌"
        }
        aborted {
            echo "Overall SUT-Dev-Pipeline ABORTED: Build was manually stopped. 🚫"
        }
    }
}