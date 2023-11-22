FROM python:3.12-alpine3.18

WORKDIR /opt/lazyconn

COPY ./lazyconn.py .
COPY ./requirements.txt .
COPY ./docker-entrypoint.sh .

RUN pip install -r ./requirements.txt
RUN apk add aws-cli openssh
RUN chmod +x ./docker-entrypoint.sh

ENV AWS_PAGER=""
ENV IS_CONTAINER="true"

ARG AWS_ACCESS_KEY_ID
ARG AWS_SECRET_ACCESS_KEY
ARG AWS_REGION="us-east-1"

RUN aws configure set aws_access_key_id $AWS_ACCESS_KEY_ID
RUN aws configure set aws_secret_access_key $AWS_SECRET_ACCESS_KEY
RUN aws configure set region $AWS_REGION

ENTRYPOINT [ "./docker-entrypoint.sh" ]