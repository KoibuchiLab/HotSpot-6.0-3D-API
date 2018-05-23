MAKE = make

CC = gcc

CFLAGS = ${WARNING} ${DEBUG}
WARNING = -Wall
DEBUG = -g
cell: cell.c
	${CC} ${CFLAGS} cell.c -o cell

clean : 
	rm -f *.o core cell
