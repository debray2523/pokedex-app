pipeline {
    agent any
    options { timeout(time: 20, unit: 'MINUTES') }
    environment {
        IMAGE = 'debray2523/pokedex-app'
        TAG   = "${env.GIT_COMMIT.take(7)}"
    }
    stages {
        stage('Checkout') {
            steps { checkout scm }
        }
        stage('Build image') {
            steps { bat 'docker build -t %IMAGE%:%TAG% .' }
        }
        stage('Test in container') {
            steps { bat 'docker run --rm %IMAGE%:%TAG% python -m pytest tests -v' }
        }
        stage('Push image') {
            when { expression { (env.BRANCH_NAME ?: env.GIT_BRANCH ?: '').endsWith('main') } }
            steps {
                withCredentials([usernamePassword(credentialsId: 'dockerhub', usernameVariable: 'U', passwordVariable: 'P')]) {
                    bat 'echo %P%| docker login -u %U% --password-stdin'
                    bat 'docker push %IMAGE%:%TAG%'
                    bat 'docker logout'
                }
            }
        }
        stage('Deploy to Minikube') {
            when { expression { (env.BRANCH_NAME ?: env.GIT_BRANCH ?: '').endsWith('main') } }
            steps {
                bat 'kubectl apply -f k8s/deployment.yaml -f k8s/service.yaml'
                bat 'kubectl set image deployment/pokedex-app pokedex-app=%IMAGE%:%TAG%'
                bat 'kubectl rollout status deployment/pokedex-app --timeout=180s'
                bat 'kubectl get pods -l app=pokedex-app'
            }
        }
    }
    post {
        success { echo "Build ${IMAGE}:${TAG} passed. If deployed, open it with: minikube service pokedex-app-service" }
        failure { echo "Build failed - see the stage that went red above." }
    }
}
