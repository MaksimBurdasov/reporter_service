import groovy.json.JsonOutput
def UUID_DIR  = UUID.randomUUID().toString()
def manifestName = 'manifest.json'
def packageName = "ossktb-rcsite-reporter-service"
def app_id = "ossktb-rcsite/middle/reporter-service"
def GIT_TAG, GIT_PUSH, version, lastCommitHash, imageFullName
def deploymentId, prev_deploy_active
def repository = "ossktb"

pipeline {
    agent {
        label {
            label 'Linux'
            customWorkspace UUID_DIR
        }
    }

    parameters {
        string(name: 'branch', description: 'branch to build', defaultValue: 'master')
        choice(name: 'artifact_target_type', choices: "RELEASE\nSNAPSHOT\nBUILD", description: '')
    }

    options {
        skipStagesAfterUnstable()
    }

    stages {
        stage('Get Tag') {
            when {
                expression {
                    params.artifact_target_type == 'RELEASE' || params.artifact_target_type == 'SNAPSHOT'
                }
            }
            steps {
                script {
                	GIT_TAG = sh(returnStdout: true, script: "commit=\$(git rev-list --tags --max-count=1); git describe --tags \$commit").trim()
                    def GIT_TAG_LAST = sh(returnStdout: true, script: "commit=\$(git rev-list HEAD --all --max-count=1); git describe --tags \$commit").trim()
                    println("Git tag: ${GIT_TAG}")
                    println("Git last tag: ${GIT_TAG_LAST}")
                    GIT_PUSH = GIT_TAG != GIT_TAG_LAST
                    if (GIT_PUSH == true) {
                        sh """
                        #Version to get the latest tag
                        A="\$(echo ${GIT_TAG}|cut -d '.' -f1)"
                        B="\$(echo ${GIT_TAG}|cut -d '.' -f2)"
                        C="\$(echo ${GIT_TAG}|cut -d '.' -f3)"
                        if [ \$C -gt 20 ]
                        then
                        if [ \$B -gt 20 ]
                        then
                        A=\$((A+1))
                        B=0 C=0
                        else
                        B=\$((B+1))
                        C=0
                        fi
                        else
                        C=\$((C+1))
                        fi
                        echo "A[\$A.\$B.\$C]">outFile """
                        nextVersion = readFile 'outFile'
                        GIT_TAG =nextVersion.substring(nextVersion.indexOf("[")+1,nextVersion.indexOf("]"));
                        echo "Adding Tag to Git '${GIT_TAG}'"
                    }
                }
            }
        }
        stage('Publish Tag') {
            when {
                expression {
                    GIT_PUSH == true
                }
            }
            steps {
                script {
                    println("Package name: ${packageName}")

                    lastCommitHash = sh(returnStdout: true, script: 'git rev-parse --short HEAD').trim()
                    println("HEAD commit hash: ${lastCommitHash}")

                    if (params.branch == 'master' && params.artifact_target_type == 'RELEASE') {
                        repository = "ossktb"
                        version = GIT_TAG

                        // publish git tag
                        withCredentials([sshUserPrivateKey(
                            credentialsId: '0042a456-1053-4028-8fc6-523709873eaa',
                            keyFileVariable: 'key')
                        ]){
                            String tag     = sh (script: "git tag -l '$version'", returnStdout: true).trim()
                            sh (script: "git tag -a $version -m 'Tag release version'")
                            sh (script: "eval `ssh-agent -s`; ssh-add $key; git push origin $version")
                        }

                    } else {
                        repository = "ossktb"
                        version = GIT_TAG + "-${lastCommitHash}-${currentBuild.number}"
                    }
                }
            }
        }
        stage('Build docker image') {
            steps {
                script {
                    registry = "${repository}.binary.alfabank.ru"
                    group = "ru/alfabank/${packageName}"
                    version = GIT_TAG

                    imageFullName  = "${registry}/${packageName}:${version}"
                    println("Image full name: ${imageFullName}")

                    def server, rtDocker
                    def buildInfo = Artifactory.newBuildInfo()

                    withCredentials([
                        usernamePassword(
                            credentialsId   : 'jenkins-artifactory',
                            usernameVariable: 'USERNAME',
                            passwordVariable: 'PASSWORD'
                        )
                    ]) {
                        def username = env.USERNAME
                        def password = env.PASSWORD

                        server    = Artifactory.newServer url: "http://binary/artifactory", username: "${username}", password: "${password}"
                        rtDocker  = Artifactory.docker server: server

                        sh("echo $PASSWORD | docker login -u $USERNAME --password-stdin $registry")

                        sh("docker build -t ${imageFullName} .")

                        sh("curl -Lo /var/lib/jenkins/.bin/jfrog --create-dirs http://binary/artifactory/banksoft/jfrog/jfrog")
                        sh("chmod +x /var/lib/jenkins/.bin/jfrog")

                        sh("/var/lib/jenkins/.bin/jfrog rt c binary --url=http://binary/artifactory --user=${username} --password=${password}")

                    }

                    url = sh(returnStdout: true, script: 'git config remote.origin.url').trim()
                    commit = sh(returnStdout: true, script: 'git rev-parse HEAD').trim()

                    rtProps = "version=${version};" +
                        "Module-Origin=${url};" +
                        "platform.deployment.app-name=${packageName};" +
                        "platform.artifact.name=${packageName};" +
                        "platform.artifact-type=service;" +
                        "platform.artifact.group=${group.replace('/', '.')};" +
                        "platform.deployment.id=${registry}/${packageName};" +
                        "platform.template.id=ru.alfabank.template.template-ufr-api;" +
                        "platform.label=API;" +
                        "platform.service.id=${registry}/${packageName};" +
                        "platform.git.branch=${params.branch};" +
                        "platform.git.repo-url=${url};" +
                        "platform.git.commit-id=${commit};" +
                        "vcs.revision=${lastCommitHash}"

                    buildInfo = rtDocker.push "${imageFullName}", "${repository}"
                    server.publishBuildInfo buildInfo
                    sh("/var/lib/jenkins/.bin/jfrog rt sp \"${repository}/${packageName}/${version}/${manifestName}\" \"${rtProps}\"")

                    def dockerImageDigest = getDockerImageDigest(imageFullName, registry, packageName)
                    echo "dockerImageDigest: $dockerImageDigest"

                    sh (script: "docker image rm '$imageFullName'")
                    sh (script: 'git checkout .')
                    sh (script: 'git clean -d -f')

                    def sha1sum = sh(script: "curl -s http://binary/artifactory/$repository/$packageName/$version/$manifestName | sha1sum | awk '{print \$1}'", returnStdout: true).trim()
                    echo "Manifest checksum $sha1sum"

                    currentBuild.description = "artifact_app_sha1:$sha1sum"
                    currentBuild.description += "\ndockerImageDigest:$dockerImageDigest"
                    currentBuild.description += "\nversion:$version"
                    currentBuild.description += "\nserviceName:$packageName"
                }
            }
        }
        stage('Deploy to Marathon') {
            steps {
                script {
                    // заменяем имэдж в джсоне для марафона
                    def old_image = "REPLACE_IMAGE"
                    def image = imageFullName

                    sh "sed -i 's#${old_image}#${image}#' marathon.json"

                    // готовим боди - убираем нью лайнз
                    body = sh(script: "tr -d '\\n\\r' < marathon.json", returnStdout: true)

                    // проверяем нет ли у аппа активных деплоев
                    prev_deploy_active = checkDeployment "$app_id"
                    if (prev_deploy_active == true){
                        def prev_deploy_alive = true
                        timeout(time: 10, unit: 'SECONDS') {
                            waitUntil {
                                script{
                                    // проверяем в деплоях
                                    prev_deploy_active = checkDeployment "$app_id"

                                    // проверяем в павших
                                    prev_deploy_alive = checkDeploymentAlive "$app_id"

                                    return(prev_deploy_active == false || prev_deploy_alive == false)
                                }
                            }
                        }
                        // если текущий деплой не жив - абортим билд но не деплой
                        if (prev_deploy_alive == false) {
                            currentBuild.result = 'ABORTED'
                            timeout(time: 1, unit: 'SECONDS') {
                                waitUntil {
                                    script{
                                        sleep 5
                                    }
                                }
                            }
                        }
                    }

                    // деплоим в марафон
                    deploymentId = deploy(app_id, body)
                    println("Deployment started:  $deploymentId")

                    // ждем пока наш деплой не появится
                    def deploy_active = false
                    catchError(stageResult: 'ABORTED'){
                        timeout(time: 10, unit: 'SECONDS') {
                            waitUntil {
                                script{
                                    deploy_active = checkDeployment "$deploymentId"
                                    return(deploy_active == true)
                                }
                            }
                        }
                    }
                    if (deploy_active!=true) {
                        println("Aborted. Deployment has no changes")
                    } else {
                        // ждем пока наш деплой не уйдет/не упадет
                        def deploy_alive = true
                        sleep(5)
                        timeout(5) {
                            waitUntil {
                                script{
                                    // проверяем в деплоях
                                    deploy_active = checkDeployment "$deploymentId"

                                    // проверяем в павших
                                    deploy_alive = checkDeploymentAlive "$app_id"
                                    println("deploy_alive: $deploy_alive")

                                    return(deploy_active == false || deploy_alive == false)
                                }
                            }
                        }
                        if (deploy_alive == false) {
                            error("Deployment failed: $deploymentId")
                        }
                    }
                }
            }
        }
    }
    post {
        failure {
            script {
                if (deploymentId) {
                deleteDeployment "$deploymentId"
                println("Deployment deleted due to failure: $deploymentId")
                }
                if (GIT_PUSH) {
                    withCredentials([sshUserPrivateKey(
                            credentialsId: '0042a456-1053-4028-8fc6-523709873eaa',
                            keyFileVariable: 'key')
                        ]){
                            sh (script: "eval `ssh-agent -s`; ssh-add $key; git push origin :refs/tags/${GIT_TAG}")
                        }
                    println("Git tag removed")
                }
            }
            println("Deployment failure")
        }
        success {
            println("Deployment successful")
        }
        aborted {
            script {
                if (prev_deploy_active == true) {
                    println("Deployment aborted due to current app deployment")
                } else {
                    println("Deployment aborted")
                }
            }
        }
    }
}

def getDockerImageDigest(
    String imageFullName,
    String registry,
    String packageName
    ){
        return sh (returnStdout: true, script: "docker inspect --format='{{index .RepoDigests 0}}' $imageFullName")
            .trim()
            .replace("$registry/$packageName" + "@", "")
    }

def getCurrentTime() {
    return java.time.LocalDateTime.now().format(java.time.format.DateTimeFormatter.ofPattern("yyyyMMdd.HHmmss"))
}

// деплоим в марафон
def deploy(String app_id, String body) {
    def url = "http://ossktbapprhel2:8080/v2/apps/$app_id"
    def response = sh(script: "curl -s -X PUT $url --data '$body' -H \"Content-Type: application/json\"", returnStdout: true)
    def responseObject = readJSON text: response
    deploymentId = "$responseObject.deploymentId"
    return deploymentId
}

// проверить есть ли деплой в активных
def checkDeployment(String id) {
    def url = "http://ossktbapprhel2:8080/v2/deployments"
    response = sh(script: "curl -s -X GET $url", returnStdout: true)
    responseObject = readJSON text: response
    str = response.split(id)[0]
    return(str != response)
}

// проверить есть ли деплой в ретраях
def checkDeploymentAlive(String app_id) {
    def url = "http://ossktbapprhel2:8080/v2/queue"
    response = sh(script: "curl -s -X GET $url", returnStdout: true)
    responseObject = readJSON text: response
    str = response.split(app_id)[0]
    return(str == response)
}

// делитим деплой в марафоне
def deleteDeployment(String id) {
    def url = "http://ossktbapprhel2:8080/v2/deployments/$id"
    def response = sh(script: "curl -s -X DELETE $url", returnStdout: true)
    def responseObject = readJSON text: response
}