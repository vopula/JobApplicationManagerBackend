pipeline {
    agent any

    environment {
        IMAGE_NAME = "job-application-manager-backend"
        IMAGE_TAG = "${env.BUILD_NUMBER}"
    }

    stages {
        stage('Build Test Image') {
            steps {
                sh 'docker build --target test -t ${IMAGE_NAME}:${IMAGE_TAG}-test .'
            }
        }

        stage('Test') {
            steps {
                sh '''
                    docker create --name test-${BUILD_NUMBER} \
                        -e PYTHONPATH=/code \
                        -e DATABASE_URL="postgresql://onlyfortest:test@localhost:5432/test" \
                        -e ENABLE_AI_EXTRACTION=false \
                        ${IMAGE_NAME}:${IMAGE_TAG}-test \
                        pytest tests --cov=. --cov-report=xml:/code/coverage.xml --junitxml=/code/test-results.xml

                    docker start -a test-${BUILD_NUMBER} || true
                    docker cp test-${BUILD_NUMBER}:/code/test-results.xml ./test-results.xml
                    docker cp test-${BUILD_NUMBER}:/code/coverage.xml ./coverage.xml
                    docker rm test-${BUILD_NUMBER}
                '''
            }
            post {
                always {
                    junit 'test-results.xml'
                }
            }
        }

        stage('SonarQube Analysis') {
            steps {
                withSonarQubeEnv('SonarQube') {
                    sh "${tool 'SonarScanner'}/bin/sonar-scanner"
                }
            }
        }

        stage('Quality Gate') {
            steps {
                timeout(time: 5, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }

        stage('Trivy Sca Scan') {
            steps {
                sh '''
                docker create --name trivy-${BUILD_NUMBER} \
                    -v /var/run/docker.sock:/var/run/docker.sock \
                    aquasec/trivy image \
                        --format json \
                        --output /tmp/trivy-report.json \
                        --severity CRITICAL,HIGH \
                        --exit-code 1 \
                        --ignore-unfixed \
                        ${IMAGE_NAME}:${IMAGE_TAG}

                docker start -a trivy-${BUILD_NUMBER}
                EXIT_CODE=$?

                docker cp trivy-${BUILD_NUMBER}:/tmp/trivy-report.json ./trivy-report.json || true
                docker rm trivy-${BUILD_NUMBER}

                exit $EXIT_CODE
                '''
            }
            post {
                always {
                    archiveArtifacts artifacts: 'trivy-report.json', allowEmptyArchive: true
                }
            }
        }

        stage('Build Production Image') {
            steps {
                sh 'docker build --target final -t ${IMAGE_NAME}:${IMAGE_TAG} .'
            }
        }
    }

    post {
        cleanup {
            sh 'docker system prune -f || true'
        }
    }
}
