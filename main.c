#include <string.h>
#include <stdint.h>

#include "forth.h"

int
main(int argc, char **argv)
{
        forth_reset();
        return (forth_run(argv[1], strlen(argv[1])));
}
