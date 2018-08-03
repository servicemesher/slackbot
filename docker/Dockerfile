FROM alpine
COPY prepare.sh /usr/local/bin
RUN /usr/local/bin/prepare.sh
COPY supervisord.conf /etc/
WORKDIR /errbot
VOLUME ["/errbot"]
CMD ["/usr/local/bin/entry.sh"]
