# Build stage
FROM eclipse-temurin:21-jdk-alpine AS build

WORKDIR /app

# Copy gradle wrapper and files
COPY gradlew ./
COPY gradlew.bat ./
COPY gradle ./gradle
COPY build.gradle ./
COPY settings.gradle ./

# Copy source code
COPY src ./src

# Build application
RUN chmod +x gradlew && ./gradlew build -x test

# Runtime stage
FROM eclipse-temurin:21-jre-alpine

# curl 및 openssh 설치 (헬스체크 및 SSH용)
RUN apk add --no-cache curl openssh \
    && mkdir -p /var/run/sshd \
    && ssh-keygen -A

WORKDIR /app

COPY --from=build /app/build/libs/cookduck-0.0.1-SNAPSHOT.jar app.jar

RUN chmod +x app.jar

# SSH 초기화 스크립트 복사
COPY init-ssh.sh /usr/local/bin/init-ssh.sh
RUN chmod +x /usr/local/bin/init-ssh.sh

EXPOSE 8080 22

# Spring Boot와 SSH를 함께 실행
ENTRYPOINT ["sh", "-c", "/usr/local/bin/init-ssh.sh & java -jar app.jar"]