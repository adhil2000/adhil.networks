CC = gcc

CFLAGS = -std=gnu99 -g -O3

default: all

all: http_client

%.o: %.c
	$(CC) -c -o $@ $< $(CFLAGS)

%: %.o
	$(CC) -o $@ $^

.PRECIOUS: %.o

.PHONY: default all

testwget:
	wget -0 real_make.html www.gnu.org/software/make/manual/make.html

testall:
	./http_client www.gnu.org 80 /software/make/manual/make.html;
	diff -s expected_output/make.html make.html
clean:
	rm -f http_client; rm -r http_client.dSYM; rm -f *.html;
