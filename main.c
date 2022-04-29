#include <sys/mman.h>

#include <unistd.h>
#include <malloc.h>
#include <string.h>
#include <stdint.h>

#include "forth.h"

int
main(int argc, char **argv)
{
	int pagesize = sysconf(_SC_PAGE_SIZE);
	void *dataspace = memalign(pagesize, 4 * pagesize);
	mprotect(dataspace, pagesize, PROT_READ|PROT_WRITE|PROT_EXEC);

        forth_reset(dataspace);
        return (forth_run(argv[1], strlen(argv[1])));
}
