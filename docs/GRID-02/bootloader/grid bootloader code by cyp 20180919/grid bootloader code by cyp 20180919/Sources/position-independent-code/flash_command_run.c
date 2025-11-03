#include <stdint.h>

#define FTFx_FSTAT_CCIF_MASK        0x80u

void flash_command_run(volatile uint8_t *reg)
{
    *reg =  FTFx_FSTAT_CCIF_MASK;

    while(!((*reg) & FTFx_FSTAT_CCIF_MASK))
    {
    }
}