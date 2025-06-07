// --- Integrated QA Stages (from your old 'Jenkinsfile.qa_tests') ---
        stage('Checkout QA Test Code') {
            steps {
                script {
                    echo "Checking out QA repository: ${QA_REPO}, branch: ${QA_BRANCH}"
                    dir('qa-code') { // Checkout into a dedicated directory
                        git branch: QA_BRANCH, credentialsId: GIT_CREDENTIAL_ID, url: QA_REPO
                    }
                }
            }
        }

        stage('Setup Python Environment (QA)') {
            steps {
                script {
                    echo "Setting up Python virtual environment and installing dependencies for QA tests..."
                    dir('qa-code') {
                        sh 'python3 -m venv ./.venv'
                        sh 'bash -c ". ./.venv/bin/activate && pip install --no-cache-dir -r requirements.txt"'
                    }
                }
            }
        }

        stage('Run QA Tests against Staging') {
            steps {
                script {
                    echo "Running Selenium tests against Staging URL: ${STAGING_URL}"
                    dir('qa-code') {
                        // CORRECTED PATHS: Use WORKSPACE directly for absolute paths
                        def qaTestAllureResultsDir = "${WORKSPACE}/${ALLURE_ROOT_DIR}/qa-tests"
                        def qaTestJunitReportFile = "${WORKSPACE}/${JUNIT_ROOT_DIR}/qa_report.xml"

                        sh "rm -rf ${qaTestAllureResultsDir}"
                        sh "mkdir -p ${qaTestAllureResultsDir}"
                        sh "mkdir -p ${WORKSPACE}/${JUNIT_ROOT_DIR}" // Ensure global JUnit reports directory exists

                        sh """#!/bin/bash
                            . ./.venv/bin/activate
                            pytest src/tests/teachers/test_teacher_signup.py --alluredir=${qaTestAllureResultsDir} --junitxml=${qaTestJunitReportFile} --browser chrome-headless --baseurl ${STAGING_URL}
                        """
                    }
                }
            }
        }

        // --- Simplified Live Deployment Stage (relies on Git push) ---
        stage('Merge Dev to Main & Push (and Trigger Live Deploy)') { // Renamed for clarity
            when {
                // This condition ensures this critical stage only runs if the entire pipeline is successful
                expression { currentBuild.result == 'SUCCESS' }
            }
            steps {
                script {
                    dir('sut-code') {
                        echo "Checking out SUT Main branch for merge operation..."
                        git branch: env.SUT_BRANCH_MAIN, credentialsId: env.GIT_CREDENTIAL_ID, url: env.SUT_REPO

                        echo "Configuring Git user for the merge commit..."
                        sh "git config user.email 'jenkins@example.com'"
                        sh "git config user.name 'Jenkins CI Automation'"

                        echo "Fetching latest ${env.SUT_BRANCH_DEV} to ensure up-to-date merge..."
                        sh "git fetch origin ${env.SUT_BRANCH_DEV}" // Fetch the dev branch as well

                        echo "Merging origin/${env.SUT_BRANCH_DEV} into ${env.SUT_BRANCH_MAIN}..."
                        // Use '--no-edit' to prevent Git from opening an editor for the merge commit message.
                        // `--no-ff` ensures a merge commit is always created, useful for history.
                        sh "git merge origin/${env.SUT_BRANCH_DEV} --no-ff --commit --no-edit -m 'Merge ${env.SUT_BRANCH_DEV} to ${env.SUT_BRANCH_MAIN} after successful QA tests [Jenkins CI]'"

                        echo "Pushing merged ${env.SUT_BRANCH_MAIN} to remote. This will trigger Render live deploy."
                        withCredentials([usernamePassword(credentialsId: env.GIT_CREDENTIAL_ID, passwordVariable: 'GIT_PAT_PASSWORD', usernameVariable: 'GIT_USERNAME')]) {
                            sh "git push https://${GIT_USERNAME}:${GIT_PAT_PASSWORD}@github.com/majd-j-kassem/majd.kassem.business.git ${env.SUT_BRANCH_MAIN}"
                        }
                        echo "SUT Main branch updated. Render will now deploy to live."

                        // --- START Smart Wait Implementation for Live Deployment ---
                        def maxAttempts = 20 // Max number of times to check (e.g., 20 * 15 seconds = 5 minutes)
                        def retryDelaySeconds = 15 // Seconds to wait between checks
                        // --- FIX: Corrected variable name from SUT_LIVE_URL to LIVE_URL ---
                        def healthCheckUrl = "${env.LIVE_URL}/health/" // Use the LIVE URL here!
                        def attempts = 0
                        def serviceHealthy = false

                        echo "Starting smart wait for live service at ${healthCheckUrl} to become healthy..."

                        while (attempts < maxAttempts && !serviceHealthy) {
                            attempts++
                            echo "Attempt ${attempts}/${maxAttempts}: Checking live service health..."
                            try {
                                // Use curl with -s (silent), -o /dev/null (discard output), -w "%{http_code}" (write HTTP code)
                                def httpCode = sh(
                                    script: "curl -s -o /dev/null -w '%{http_code}' ${healthCheckUrl}",
                                    returnStdout: true
                                ).trim()

                                echo "Received HTTP status code: ${httpCode}"

                                if (httpCode == '200') {
                                    serviceHealthy = true
                                    echo "Live service at ${healthCheckUrl} is healthy!"
                                } else {
                                    echo "Live service not yet healthy. Retrying in ${retryDelaySeconds} seconds..."
                                    sleep retryDelaySeconds
                                }
                            } catch (e) {
                                echo "Error checking health: ${e.getMessage()}. Retrying in ${retryDelaySeconds} seconds..."
                                sleep retryDelaySeconds
                            }
                        }

                        if (!serviceHealthy) {
                            error "Live service at ${healthCheckUrl} did not become healthy within ${maxAttempts * retryDelaySeconds} seconds. Failing pipeline."
                        }
                        // --- END Smart Wait Implementation ---
                    } // End of dir('sut-code')
                } // End of script block
            } // End of steps block
        } // End of stage block
    }
