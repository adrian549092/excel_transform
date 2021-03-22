
pipeline {
  agent any
  stages {
    stage('Skip Check') {
      steps {
        scmSkip(deleteBuild: false, skipPattern:'.*\\[ci skip\\].*')
      }
    }
    stage('Build') {
      parallel {
        stage('Build binaries') {
          steps {
            sh '''python -m build'''
          }
        }
      }
    }
    stage('Deploy') {
      parallel {
        stage('Deploy binaries to Nexus Repository') {
          steps {
            sh '''python -m twine upload --repository pypi dist/*'''
          }
        }
      }
    }
  }
}