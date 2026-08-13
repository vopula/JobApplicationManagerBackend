pipeline {
    agent any

    environment {
        DOCKERHUB_CREDENTIALS = credentials('jenkins-local-to-docker-hub')
        IMAGE_NAME = "${DOCKERHUB_CREDENTIALS_USR}/job-application-manager-backend"
        IMAGE_TAG = "${env.BUILD_NUMBER}"
    }

    stages {
        stage('Trivy Secret Scan') {
            steps {
                sh '''
                    docker create --name secret-${BUILD_NUMBER} \
                        aquasec/trivy fs \
                            --scanners secret \
                            --format json \
                            --output /tmp/secret-report.json \
                            --exit-code 1 \
                            --skip-dirs .git \
                            /workspace

                    docker cp . secret-${BUILD_NUMBER}:/workspace

                    set +e
                    docker start -a secret-${BUILD_NUMBER}
                    EXIT_CODE=$?
                    set -e

                    docker cp secret-${BUILD_NUMBER}:/tmp/secret-report.json ./secret-report.json
                    docker rm secret-${BUILD_NUMBER}

                    exit $EXIT_CODE
                '''
            }
            post {
                always {
                    archiveArtifacts artifacts: 'secret-report.json', allowEmptyArchive: true
                }
            }
        }

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

        stage('Build Production Image') {
            steps {
                sh 'docker build --pull --target final -t ${IMAGE_NAME}:${IMAGE_TAG} .'
            }
        }

        stage('Trivy Sca And Image Scan') {
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

                set +e
                docker start -a trivy-${BUILD_NUMBER}
                EXIT_CODE=$?
                set -e

                docker cp trivy-${BUILD_NUMBER}:/tmp/trivy-report.json ./trivy-report.json
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

        stage('Trivy IaC Scan') {
            steps {
                sh '''
                    rm -rf ./_iac_ctx && mkdir -p ./_iac_ctx
                    cp Dockerfile ./_iac_ctx/

                    docker create --name iac-${BUILD_NUMBER} \
                        aquasec/trivy config \
                            --format json \
                            --output /tmp/iac-report.json \
                            --severity CRITICAL,HIGH \
                            --exit-code 1 \
                            /workspace

                    docker cp ./_iac_ctx iac-${BUILD_NUMBER}:/workspace

                    set +e
                    docker start -a iac-${BUILD_NUMBER}
                    EXIT_CODE=$?
                    set -e

                    docker cp iac-${BUILD_NUMBER}:/tmp/iac-report.json ./iac-report.json
                    docker rm iac-${BUILD_NUMBER}
                    rm -rf ./_iac_ctx

                    exit $EXIT_CODE
                '''
            }
            post {
                always {
                    archiveArtifacts artifacts: 'iac-report.json', allowEmptyArchive: true
                }
            }
        }

        stage('Docker Login') {
            steps {
                sh 'echo $DOCKERHUB_CREDENTIALS_PSW | docker login -u $DOCKERHUB_CREDENTIALS_USR --password-stdin'
            }
        }

        stage('Push to Docker Hub') {
            steps {
                sh "docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${IMAGE_NAME}:latest"
                sh "docker push ${IMAGE_NAME}:${IMAGE_TAG}"
                sh "docker push ${IMAGE_NAME}:latest"
            }
        }
    }

    post {
        cleanup {
            sh 'docker system prune -f --filter "until=24h" || true'
            sh 'docker logout || true'
        }
    }
}
