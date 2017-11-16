FROM debian:jessie

RUN apt-get update && apt-get install -y build-essential python-dev python-pip python-dateutil

COPY ./ /project-dev-kpis/
RUN cat /project-dev-kpis/requirements.txt
RUN pip install --upgrade pip
RUN pip install --upgrade $(cat /project-dev-kpis/requirements.txt | tr '\n' ' ')

EXPOSE 80 8080

ENTRYPOINT [ "/project-dev-kpis/run-api", "--projects-config=/projects.json" ]
