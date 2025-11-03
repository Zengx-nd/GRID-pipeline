#include "bl_bsp.h"
#include "bl_core.h"
#include "bl_cfg.h"
#include <stdint.h>

#include "derivative.h" /* include peripheral declarations */
#include "UART.h"
#include "CLK.h"
/*
*
*  Definitions
*
*/
static const uint32_t crc_tab[256] =
{
0x00000000, 0xF26B8303, 0xE13B70F7, 0x1350F3F4, 0xC79A971F, 0x35F1141C, 0x26A1E7E8, 0xD4CA64EB,
0x8AD958CF, 0x78B2DBCC, 0x6BE22838, 0x9989AB3B, 0x4D43CFD0, 0xBF284CD3, 0xAC78BF27, 0x5E133C24,
0x105EC76F, 0xE235446C, 0xF165B798, 0x030E349B, 0xD7C45070, 0x25AFD373, 0x36FF2087, 0xC494A384,
0x9A879FA0, 0x68EC1CA3, 0x7BBCEF57, 0x89D76C54, 0x5D1D08BF, 0xAF768BBC, 0xBC267848, 0x4E4DFB4B,
0x20BD8EDE, 0xD2D60DDD, 0xC186FE29, 0x33ED7D2A, 0xE72719C1, 0x154C9AC2, 0x061C6936, 0xF477EA35,
0xAA64D611, 0x580F5512, 0x4B5FA6E6, 0xB93425E5, 0x6DFE410E, 0x9F95C20D, 0x8CC531F9, 0x7EAEB2FA,
0x30E349B1, 0xC288CAB2, 0xD1D83946, 0x23B3BA45, 0xF779DEAE, 0x05125DAD, 0x1642AE59, 0xE4292D5A,
0xBA3A117E, 0x4851927D, 0x5B016189, 0xA96AE28A, 0x7DA08661, 0x8FCB0562, 0x9C9BF696, 0x6EF07595,
0x417B1DBC, 0xB3109EBF, 0xA0406D4B, 0x522BEE48, 0x86E18AA3, 0x748A09A0, 0x67DAFA54, 0x95B17957,
0xCBA24573, 0x39C9C670, 0x2A993584, 0xD8F2B687, 0x0C38D26C, 0xFE53516F, 0xED03A29B, 0x1F682198,
0x5125DAD3, 0xA34E59D0, 0xB01EAA24, 0x42752927, 0x96BF4DCC, 0x64D4CECF, 0x77843D3B, 0x85EFBE38,
0xDBFC821C, 0x2997011F, 0x3AC7F2EB, 0xC8AC71E8, 0x1C661503, 0xEE0D9600, 0xFD5D65F4, 0x0F36E6F7,
0x61C69362, 0x93AD1061, 0x80FDE395, 0x72966096, 0xA65C047D, 0x5437877E, 0x4767748A, 0xB50CF789,
0xEB1FCBAD, 0x197448AE, 0x0A24BB5A, 0xF84F3859, 0x2C855CB2, 0xDEEEDFB1, 0xCDBE2C45, 0x3FD5AF46,
0x7198540D, 0x83F3D70E, 0x90A324FA, 0x62C8A7F9, 0xB602C312, 0x44694011, 0x5739B3E5, 0xA55230E6,
0xFB410CC2, 0x092A8FC1, 0x1A7A7C35, 0xE811FF36, 0x3CDB9BDD, 0xCEB018DE, 0xDDE0EB2A, 0x2F8B6829,
0x82F63B78, 0x709DB87B, 0x63CD4B8F, 0x91A6C88C, 0x456CAC67, 0xB7072F64, 0xA457DC90, 0x563C5F93,
0x082F63B7, 0xFA44E0B4, 0xE9141340, 0x1B7F9043, 0xCFB5F4A8, 0x3DDE77AB, 0x2E8E845F, 0xDCE5075C,
0x92A8FC17, 0x60C37F14, 0x73938CE0, 0x81F80FE3, 0x55326B08, 0xA759E80B, 0xB4091BFF, 0x466298FC,
0x1871A4D8, 0xEA1A27DB, 0xF94AD42F, 0x0B21572C, 0xDFEB33C7, 0x2D80B0C4, 0x3ED04330, 0xCCBBC033,
0xA24BB5A6, 0x502036A5, 0x4370C551, 0xB11B4652, 0x65D122B9, 0x97BAA1BA, 0x84EA524E, 0x7681D14D,
0x2892ED69, 0xDAF96E6A, 0xC9A99D9E, 0x3BC21E9D, 0xEF087A76, 0x1D63F975, 0x0E330A81, 0xFC588982,
0xB21572C9, 0x407EF1CA, 0x532E023E, 0xA145813D, 0x758FE5D6, 0x87E466D5, 0x94B49521, 0x66DF1622,
0x38CC2A06, 0xCAA7A905, 0xD9F75AF1, 0x2B9CD9F2, 0xFF56BD19, 0x0D3D3E1A, 0x1E6DCDEE, 0xEC064EED,
0xC38D26C4, 0x31E6A5C7, 0x22B65633, 0xD0DDD530, 0x0417B1DB, 0xF67C32D8, 0xE52CC12C, 0x1747422F,
0x49547E0B, 0xBB3FFD08, 0xA86F0EFC, 0x5A048DFF, 0x8ECEE914, 0x7CA56A17, 0x6FF599E3, 0x9D9E1AE0,
0xD3D3E1AB, 0x21B862A8, 0x32E8915C, 0xC083125F, 0x144976B4, 0xE622F5B7, 0xF5720643, 0x07198540,
0x590AB964, 0xAB613A67, 0xB831C993, 0x4A5A4A90, 0x9E902E7B, 0x6CFBAD78, 0x7FAB5E8C, 0x8DC0DD8F,
0xE330A81A, 0x115B2B19, 0x020BD8ED, 0xF0605BEE, 0x24AA3F05, 0xD6C1BC06, 0xC5914FF2, 0x37FACCF1,	
0x69E9F0D5, 0x9B8273D6, 0x88D28022, 0x7AB90321, 0xAE7367CA, 0x5C18E4C9, 0x4F48173D, 0xBD23943E,
0xF36E6F75, 0x0105EC76, 0x12551F82, 0xE03E9C81, 0x34F4F86A, 0xC69F7B69, 0xD5CF889D, 0x27A40B9E,
0x79B737BA, 0x8BDCB4B9, 0x988C474D, 0x6AE7C44E, 0xBE2DA0A5, 0x4C4623A6, 0x5F16D052, 0xAD7D5351
};
#define Success 0x01
#define Fail 0x00
#define kFramingPacketType_Start 0xc6
#define kFramingPacketType_StartReply 0x99
#define kFramingPacketType_ReceiveUpdateReply 0x98
#define kFramingPacketType_Update 0xc7

#define Grid 0x19
#define PayLoad 0x11

void Enable_Interrupt(UINT8 vector_number);
void Uart_Interrupt (UINT8 data); 

typedef int32_t status_t;
uint32_t TEST_CRC = 0;
uint32_t TEST_VALUE_SUM = 0;

enum
{
    kCallbackBufferSize = 64,
    kPacket_MaxPayloadSize = 32,
};

//! @brief Serial framing packet constants.
enum _framing_packet_constants
{
    kFramingPacketStartByte         = 0x5a,
    kFramingPacketType_Ack          = 0xa1,
    kFramingPacketType_Nak          = 0xa2,
    kFramingPacketType_AckAbort     = 0xa3,
    kFramingPacketType_Command      = 0xa4,
    kFramingPacketType_Data         = 0xa5,
    kFramingPacketType_Ping         = 0xa6,
    kFramingPacketType_PingResponse = 0xa7
};

enum
{
		kPacketState_StartByte_1,
		kPacketState_StartByte_2,
		kPacketState_StartByte_3,
		kPacketState_StartByte_4,
			kPacketState_Length,
		kPacketState_ReceiveAll
};

enum
{
    kStatus_Success             = 0,
    kStatus_Fail                = 1,
    kStatus_InvalidArgument     = 4,
    kStatus_Busy                = 15,
    kStatus_UnknownProperty     = 10300,

    kStatus_FlashAlignmentError = 101,
    kStatus_FlashAccessError = 103,
    kStatus_FlashProtectionViolation = 104,
    kStatus_FlashCommandFailure = 105,
    
    kStatusMemoryRangeInvalid = 10200,
};

union ProgameStart_packet_t
{
	uint8_t param[22];
	struct{
    uint8_t startByte[4];
		uint8_t lengthInBytes[2];
	  uint8_t destinationuser;
		uint8_t sourceuser;
 		uint8_t framecount[2];
    uint8_t frameType;
    uint8_t packetType;
		uint8_t versionnumber;
		uint8_t fileID;		
		uint8_t totalupdatenum[3];
		uint8_t sumvalue;
		uint8_t endByte[4];
	}data;
};
union SoftwareStart_packet_t
{
	uint8_t param[19];
	struct{
    uint8_t startByte[4];
		uint8_t lengthInBytes[2];
	  uint8_t destinationuser;
		uint8_t sourceuser;
 		uint8_t framecount[2];
    uint8_t frameType;
    uint8_t packetType;
		uint8_t versionnumber;
		uint8_t fileID;		
		uint8_t sumvalue;
		uint8_t endByte[4];
	}data;
};
union packet_response
{
	uint8_t param[19];
	struct{
    uint8_t startByte[4];
		uint8_t lengthInBytes[2];
	  uint8_t destinationuser;
		uint8_t sourceuser;
 		uint8_t framecount[2];
    uint8_t frameType;
    uint8_t reponseType;
		uint8_t versionnumber;
		uint8_t fileID;
		uint8_t sumvalue;
		uint8_t endByte[4];
	}data;
};
union Code_4096_packet_data
{
	uint8_t param[33];
	struct{
    uint8_t startByte[4];
    uint8_t lengthInBytes[2];	
		uint8_t destinationuser;
		uint8_t sourceuser;
		uint8_t framecount[2];
    uint8_t frameType;
		uint8_t versionnumber;
		uint8_t fileID;
		uint8_t updatenumber[3];
		uint8_t startaddress[4];
		uint8_t endaddress[4];
  //  uint32_t payload[4096/sizeof(uint32_t)];
		// uint8_t payload[4096];
    uint8_t crc32[4];
		uint8_t checkvalue;
		uint8_t endByte[4];
	}packet_data;
};
typedef struct
{
		uint8_t versionnumber;
		uint8_t fileID;
    uint8_t  state;
		uint32_t totalpacketnum;
		uint32_t Updatapacketnum;
    uint32_t address;
    uint32_t count;
		uint16_t framecount;
		uint16_t code;
}bootloader_context_t;
/******************************************************************

        FLASH related definitions, functions and local variables

*******************************************************************/
//! @name Flash controller command numbers
//@{
#define FTFx_VERIFY_BLOCK                  0x00 //!< RD1BLK
#define FTFx_VERIFY_SECTION                0x01 //!< RD1SEC
#define FTFx_PROGRAM_CHECK                 0x02 //!< PGMCHK
#define FTFx_READ_RESOURCE                 0x03 //!< RDRSRC
#define FTFx_PROGRAM_LONGWORD              0x06 //!< PGM4
#define FTFx_PROGRAM_PHRASE                0x07 //!< PGM8
#define FTFx_ERASE_BLOCK                   0x08 //!< ERSBLK
#define FTFx_ERASE_SECTOR                  0x09 //!< ERSSCR
#define FTFx_PROGRAM_SECTION               0x0B //!< PGMSEC
#define FTFx_VERIFY_ALL_BLOCK              0x40 //!< RD1ALL
#define FTFx_READ_ONCE                     0x41 //!< RDONCE
#define FTFx_PROGRAM_ONCE                  0x43 //!< PGMONCE
#define FTFx_ERASE_ALL_BLOCK               0x44 //!< ERSALL
#define FTFx_SECURITY_BY_PASS              0x45 //!< VFYKEY
#define FTFx_ERASE_ALL_BLOCK_UNSECURE      0x49 //!< ERSALLU
#define FTFx_SWAP_CONTROL                  0x46 //!< SWAP
#define FTFx_SET_FLEXRAM_FUNCTION          0x81 //!< SETRAM
//@}

#if defined (FTFE)
#define FTFx    FTFE
#define BL_FEATURE_PROGRAM_PHASE    1
#elif defined (FTFL)
#define FTFx    FTFL
#define BL_FEATURE_PROGRAM_PHASE    0
#elif defined (FTFA)
#define FTFx    FTFA
#define BL_FEATURE_PROGRAM_PHASE    0
#elif defined (FTMRE)
#define FTFx    FTMRE
#define BL_FEATURE_PROGRAM_PHASE    0
#endif //

#define FTFx_FSTAT_CCIF_MASK        0x80u
#define FTFx_FSTAT_RDCOLERR_MASK    0x40u
#define FTFx_FSTAT_ACCERR_MASK      0x20u
#define FTFx_FSTAT_FPVIOL_MASK      0x10u
#define FTFx_FSTAT_MGSTAT0_MASK     0x01u
#define FTFx_FSEC_SEC_MASK          0x03u


volatile uint32_t* const kFCCOBx =
#if defined(FTFE)
(volatile uint32_t*)&FTFE->FCCOB3;
#elif defined (FTEL)
(volatile uint32_t*)&FTFL->FCCOB3;
#elif defined (FTFA)
(volatile uint32_t*)&FTFA->FCCOB3;
#elif defined (FTMRE)  
(volatile uint32_t*)&FTMRE->FCCOBIX;
#endif

const uint8_t s_flash_command_run[] = 
    {0x00, 0xB5, 0x80, 0x21, 0x01, 0x70, 0x01, 0x78, 0x09, 0x06, 0xFC, 0xD5,0x00, 0xBD};
static uint32_t s_flash_ram_function[8];
typedef void (*flash_run_entry_t)(volatile uint8_t *reg);
flash_run_entry_t s_flash_run_entry;
static status_t flash_program(uint32_t start, uint32_t *src, uint32_t length);
static status_t flash_erase(uint32_t start, uint32_t length);
#if BL_FEATURE_VERIFY
static status_t flash_verify_program(uint32_t start, const uint32_t *expectedData, uint32_t length);
#endif
static void flash_init(void);

/*****************************************************************************************

Packet related definitions, functions and virables.

******************************************************************************************/
static union ProgameStart_packet_t Grid_ProgrameStart_Packet;
static union SoftwareStart_packet_t Grid_SoftwareStart_Packet;
static union  packet_response Grid_Response_Packet;
static union  Code_4096_packet_data Grid_4096_Code_Packet;
static uint8_t read_byte(void);
static status_t serial_packet_read();
/*
*   Local functions
*/
#define FTMRH           FTMRE
#define FLASH_ERR_BASE				0x3000										/*!< FTMRH error base */
#define FLASH_ERR_SUCCESS			0													/*!< FTMRH sucess */
#define FLASH_ERR_INVALID_PARAM		(FLASH_ERR_BASE+1)		/*!<  invalid parameter error code*/
#define EEPROM_ERR_SINGLE_BIT_FAULT	(FLASH_ERR_BASE+2)	/*!<  EEPROM single bit fault error code*/
#define EEPROM_ERR_DOUBLE_BIT_FAULT	(FLASH_ERR_BASE+4)	/*!<  EEPROM double bits fault error code*/
#define FLASH_ERR_ACCESS			(FLASH_ERR_BASE+8)				/*!< flash access error code*/
#define FLASH_ERR_PROTECTION		(FLASH_ERR_BASE+0x10)		/*!<  flash protection error code*/
#define FLASH_ERR_MGSTAT0			(FLASH_ERR_BASE+0x11)			/*!<  flash verification error code*/
#define FLASH_ERR_MGSTAT1			(FLASH_ERR_BASE+0x12)			/*!<  flash non-correctable error code*/
#define FLASH_ERR_INIT_CCIF			(FLASH_ERR_BASE+0x14)		/*!<  flash driver init error with CCIF = 1*/
#define FLASH_ERR_INIT_FDIV			(FLASH_ERR_BASE+0x18)		/*!<  flash driver init error with wrong FDIV*/ 

#define FTMRH_CMD_ERASE_VERIFY_ALL				0x01			/*!< FTMRH erase verify all command */
#define FTMRH_CMD_ERASE_VERIFY_BLOCK			0x02			/*!< FTMRH erase verify block command */
#define FTMRH_CMD_ERASE_ALL								0x08			/*!< FTMRH erase all command */
#define FTMRH_CMD_ERASE_BLOCK							0x09			/*!< FTMRH erase blockcommand */
#define FTMRH_CMD_UNSECURE								0x0B			/*!< FTMRH unsecure command */
#define FTMRH_CMD_SET_USER_MARGIN					0x0D			/*!< FTMRH set usermargin command */

#define FLASH_CMD_ERASE_VERIFY_SECTION		0x03			/*!< FTMRH erase verify section command */
#define FLASH_CMD_READONCE								0x04			/*!< FTMRH read once command */
#define FLASH_CMD_PROGRAM									0x06			/*!< FTMRH program command */
#define FLASH_CMD_PROGRAMONCE							0x07			/*!< FTMRH program once command */
#define FLASH_CMD_ERASE_SECTOR						0x0A			/*!< FTMRH erase sector command */
#define FLASH_CMD_BACKDOOR_ACCESS					0x0C			/*!< FTMRH backdoor key access command */
#define FLASH_CMD_SET_USER_MARGIN_LEVEL		0x0D			/*!< FTMRH set user margin level command */

#define EEPROM_CMD_ERASE_VERIFY_SECTION		0x10			/*!< EEPROM erase berify section command */
#define EEPROM_CMD_PROGRAM								0x11			/*!< EEPROM program command */
#define EEPROM_CMD_ERASE_SECTOR 					0x12			/*!< EEPROM erase sector command */


#define FTMRH_FSTAT_ACCERR_MASK         FTMRE_FSTAT_ACCERR_MASK 
#define FTMRH_FSTAT_FPVIOL_MASK         FTMRE_FSTAT_FPVIOL_MASK   
#define FTMRH_FSTAT_MGSTAT0_MASK  (1)						/*!< FTMRH FSTAT MGSTAT0 MASK */
#define FTMRH_FSTAT_MGSTAT1_MASK  (1<<1)				/*!< FTMRH FSTAT MGSTAT1 MASK */
#define FTMRH_FSTAT_CCIF_MASK           FTMRE_FSTAT_CCIF_MASK  
void FLASH_LaunchCMD(uint8_t bWaitComplete)
{
#if     defined(FLASH_ENABLE_STALLING_FLASH_CONTROLLER)
     MCM->PLACR |= MCM_PLACR_ESFC_MASK;          /* enable stalling flash controller when flash is busy */
#endif
    FTMRH->FSTAT = 0x80;    
    if(bWaitComplete)
    {
      // Wait till command is completed
      while (!(FTMRH->FSTAT & FTMRH_FSTAT_CCIF_MASK));
    }
}
uint16_t FLASH_EraseSector(uint32_t u32NVMTargetAddress)
{
	uint16_t u16Err = FLASH_ERR_SUCCESS;
	
	// Check address to see if it is aligned to 4 bytes
	// Global address [1:0] must be 00.
	if(u32NVMTargetAddress & 0x03)
	{
		u16Err = FLASH_ERR_INVALID_PARAM;
		return (u16Err);
	}
	// Clear error flags
	FTMRH->FSTAT = 0x30;
	
	// Write index to specify the command code to be loaded
	FTMRH->FCCOBIX = 0x0;
	// Write command code and memory address bits[23:16]	
	FTMRH->FCCOBHI = FLASH_CMD_ERASE_SECTOR;// EEPROM FLASH command
	FTMRH->FCCOBLO = u32NVMTargetAddress>>16;// memory address bits[23:16]
	// Write index to specify the lower byte memory address bits[15:0] to be loaded
	FTMRH->FCCOBIX = 0x1;
	// Write the lower byte memory address bits[15:0]
	FTMRH->FCCOBLO = u32NVMTargetAddress;
	FTMRH->FCCOBHI = u32NVMTargetAddress>>8;
	
	// Launch the command
	FLASH_LaunchCMD(1);
	
	// Check error status
	if(FTMRH->FSTAT & FTMRH_FSTAT_ACCERR_MASK)
	{
		u16Err |= FLASH_ERR_ACCESS;
	}
	if(FTMRH->FSTAT & FTMRH_FSTAT_FPVIOL_MASK)
	{
		u16Err |= FLASH_ERR_PROTECTION;		
	}
	if(FTMRH->FSTAT & FTMRH_FSTAT_MGSTAT0_MASK)
	{
		u16Err |= FLASH_ERR_MGSTAT0;		
	}
	if(FTMRH->FSTAT & FTMRH_FSTAT_MGSTAT1_MASK)
	{
		u16Err |= FLASH_ERR_MGSTAT1;		
	}	
#if defined(CPU_KEA8) 
	if(FTMRH->FERSTAT & (FTMRH_FERSTAT_SFDIF_MASK))
	{
		u16Err |= EEPROM_ERR_SINGLE_BIT_FAULT;
	}
	if(FTMRH->FERSTAT & (FTMRH_FERSTAT_DFDIF_MASK))
	{
		u16Err |= EEPROM_ERR_DOUBLE_BIT_FAULT;
	}
#endif	
	return (u16Err);
}
uint16_t FLASH_EraseVerifySection(uint32_t u32NVMTargetAddress, uint16_t u16LongWordCount)
{
	uint16_t u16Err = FLASH_ERR_SUCCESS;
	// Check address to see if it is aligned to 4 bytes
	// Global address [1:0] must be 00.
	if(u32NVMTargetAddress & 0x03)
	{
		u16Err = FLASH_ERR_INVALID_PARAM;
		return (u16Err);
	}	
	// Clear error flags
	FTMRH->FSTAT = 0x30;
	
	// Write index to specify the command code to be loaded
	FTMRH->FCCOBIX = 0x0;
	// Write command code and memory address bits[23:16]	
	FTMRH->FCCOBHI = FLASH_CMD_ERASE_VERIFY_SECTION;// erase verify FLASH section command
	FTMRH->FCCOBLO = u32NVMTargetAddress>>16;// memory address bits[23:16] with bit23 = 0 for Flash block, 1 for EEPROM block
	// Write index to specify the lower byte memory address bits[15:0] to be loaded
	FTMRH->FCCOBIX = 0x1;
	// Write the lower byte memory address bits[15:0]
	FTMRH->FCCOBLO = u32NVMTargetAddress;
	FTMRH->FCCOBHI = u32NVMTargetAddress>>8;

	// Write index to specify the # of longwords to be verified
	FTMRH->FCCOBIX = 0x2;
	// Write the # of longwords 
	FTMRH->FCCOBLO = u16LongWordCount;
	FTMRH->FCCOBHI = u16LongWordCount>>8;
	
	// Launch the command
	FLASH_LaunchCMD(1);
	
	// Check error status
	if(FTMRH->FSTAT & FTMRH_FSTAT_ACCERR_MASK)
	{
		u16Err |= FLASH_ERR_ACCESS;
	}
	if(FTMRH->FSTAT & FTMRH_FSTAT_MGSTAT0_MASK)
	{
		u16Err |= FLASH_ERR_MGSTAT0;		
	}
	if(FTMRH->FSTAT & FTMRH_FSTAT_MGSTAT1_MASK)
	{
		u16Err |= FLASH_ERR_MGSTAT1;		
	}	
#if defined(CPU_KEA8) 
	if(FTMRH->FERSTAT & (FTMRH_FERSTAT_SFDIF_MASK))
	{
		u16Err |= EEPROM_ERR_SINGLE_BIT_FAULT;
	}
	if(FTMRH->FERSTAT & (FTMRH_FERSTAT_DFDIF_MASK))
	{
		u16Err |= EEPROM_ERR_DOUBLE_BIT_FAULT;
	}
#endif
#if 0	
	if(FTMRH->FSTAT & FTMRH_FSTAT_FPVIOL_MASK)
	{
		u16Err |= FLASH_ERR_PROTECTION;		
	}
#endif	
	return (u16Err);
}

static uint8_t XOR_Operation(uint8_t* buffer,uint32_t size)
{
    uint32_t i;
    uint8_t result;
    result = buffer[0]^buffer[1];
    for(i=2;i<size;i++)
    {
        result ^=  buffer[i];
    }
    return result;
}
static void application_run(uint32_t sp, uint32_t pc);
__STATIC_INLINE uint32_t align_down(uint32_t data, uint32_t base)
{
    return (data & ~(base-1));
}

__STATIC_INLINE uint32_t align_up(uint32_t data, uint32_t base)
{
    return align_down(data + base - 1, base);
}

static bool is_application_valid(uint32_t sp, uint32_t pc)
{
    bool spValid = ((sp > TARGET_RAM_START) && (sp <=(TARGET_RAM_START+TARGET_RAM_SIZE)));
    bool pcValid = ((pc >=APPLICATION_BASE) && (pc < TARGET_FLASH_SIZE));
    
    return spValid && pcValid;
}


/*
*   Local variables
*/
static bootloader_context_t bl_ctx;


/**********************************************************************************
*  
*               Code
*
***********************************************************************************/
#define NULL 0
void crc16_update(uint16_t *currectCrc, const uint8_t *src, uint32_t lengthInBytes)
{
    uint32_t crc = *currectCrc;
    uint32_t j;
    for (j=0; j < lengthInBytes; ++j)
    {
        uint32_t i;
        uint32_t byte = src[j];
        crc ^= byte << 8;
        for (i = 0; i < 8; ++i)
        {
            uint32_t temp = crc << 1;
            if (crc & 0x8000)
            {
                temp ^= 0x1021;
            }
            crc = temp;
        }
    } 
    *currectCrc = crc;
}

uint32_t csp_crc32_memory(const uint8_t * data, uint32_t length)
{
uint32_t crc;
if (data == NULL || length == 0)
return 0;
crc = 0xFFFFFFFF;
while (length --)
crc = crc_tab[(crc ^ *data++) & 0xFFL] ^ (crc >> 8);
return (crc ^ 0xFFFFFFFF);
}


static uint8_t read_byte(void)
{
    return bl_hw_if_read_byte();
}
//static union ProgameStart_packet_t Grid_ProgrameStart_Packet;
//static union SoftwareStart_packet_t Grid_SoftwareStart_Packet;
//static union  packet_response Grid_Response_Packet;
//static union  Code_packet_data Grid_Code_Packet;
uint16_t Packet_Length;
  uint32_t s_stateCnt;
uint32_t crcvalue;
uint8_t crcvalue_arr[4];
uint32_t grid_startaddress;
uint32_t grid_endaddress;
	uint8_t sum =0;
uint8_t flag_state  = 0;
								#define FLASH_SECTOR_SIZE 512
static status_t serial_packet_read()
{
  static int32_t s_packetState = kPacketState_StartByte_1;
	static uint8_t receive_buffer[4129];

	uint32_t i = 0;
	uint8_t value_sum = 0;

  bool isPacketComplete = false;
  bool hasMoreData = false;
	    status_t status = kStatus_Success;
    uint8_t tmp;
    tmp = read_byte();
			switch(s_packetState)
			{
				case kPacketState_StartByte_1:
						if (tmp == 0x1A)
						{
									s_stateCnt = 0;
							receive_buffer[s_stateCnt++] = tmp;
							s_packetState = kPacketState_StartByte_2;
						}
						else
						{
							s_stateCnt = 0;
							s_packetState = kPacketState_StartByte_1;					
						}

						break;
				case kPacketState_StartByte_2:
					 if(tmp == 0xCF)
						{
							receive_buffer[s_stateCnt++] = tmp;
							s_packetState = kPacketState_StartByte_3;
						}
						else
						{
							s_stateCnt = 0;
							s_packetState = kPacketState_StartByte_1;
						}
						break;
				case kPacketState_StartByte_3:
					 if(tmp == 0xFC)
						{
							receive_buffer[s_stateCnt++] = tmp;
							s_packetState = kPacketState_StartByte_4;
						}
						else
						{
							s_stateCnt = 0;
							s_packetState = kPacketState_StartByte_1;
						}
						break;
				case kPacketState_StartByte_4:
					 if(tmp == 0X1D)
						{
							receive_buffer[s_stateCnt++] = tmp;
							s_packetState = kPacketState_Length;
						}
						else
						{
							s_stateCnt = 0;
							s_packetState = kPacketState_StartByte_1;
						}
						break;
				case kPacketState_Length:
							receive_buffer[s_stateCnt++] = tmp;
								if(s_stateCnt >=6)
								{	
									Packet_Length =  (receive_buffer[4]*256 + receive_buffer[5]) + 11;
									s_packetState = kPacketState_ReceiveAll;	
									s_stateCnt = 6;											
								}		
					break;
				case kPacketState_ReceiveAll:

							receive_buffer[s_stateCnt++] = tmp;	
											    
								if(s_stateCnt >= Packet_Length)
								{
				
										isPacketComplete = true;								
										s_stateCnt = 0;
										s_packetState = kPacketState_StartByte_1;	
										break;									
								}


								
					break;
			}	
		if(isPacketComplete == true)
		{
			switch(receive_buffer[10])
			{
				case 0xc6:
					for(i = 0; i< 22;i++)
					{
						Grid_ProgrameStart_Packet.param[i] = receive_buffer[i];							
					}
					break;
				case 0xc7:
					
					if(Packet_Length == 4129)
					{				

							for(i = 0; i < 24; i++)
							{
								Grid_4096_Code_Packet.param[i] = receive_buffer[i];
							}						
						Grid_4096_Code_Packet.param[24] = receive_buffer[4120];		
						Grid_4096_Code_Packet.param[25] = receive_buffer[4121];	
						Grid_4096_Code_Packet.param[26] = receive_buffer[4122];	
						Grid_4096_Code_Packet.param[27] =receive_buffer[4123];
							
					  Grid_4096_Code_Packet.param[28] =receive_buffer[4124];
						
						Grid_4096_Code_Packet.param[29] = receive_buffer[4125];
						Grid_4096_Code_Packet.param[30] = receive_buffer[4126];
						Grid_4096_Code_Packet.param[31] = receive_buffer[4127];
						Grid_4096_Code_Packet.param[32] = receive_buffer[4128];
						
					}
					else
					{							
					}
					break;
				case 0xc8:
					for(i = 0; i< 19;i++)
					{
						Grid_SoftwareStart_Packet.param[i] = receive_buffer[i];							
					}

					break;
			}
			switch(receive_buffer[10])
			{
				case 0xc6:
						//bl_ctx.state = 0xc6;
						if(Grid_ProgrameStart_Packet.data.startByte[0] == 0x1A
							&&Grid_ProgrameStart_Packet.data.startByte[1] == 0xCF
						&&Grid_ProgrameStart_Packet.data.startByte[2] == 0XFC&&Grid_ProgrameStart_Packet.data.startByte[3] == 0X1D)
						{
							if(Grid_ProgrameStart_Packet.data.lengthInBytes[1] == 0x0B)
							{
								if(Grid_ProgrameStart_Packet.data.destinationuser == Grid)
								{
									if(Grid_ProgrameStart_Packet.data.sourceuser == PayLoad)
									{
										if(Grid_ProgrameStart_Packet.data.frameType == 0xc6)
										{
											sum = 0;
										sum = 	XOR_Operation(&Grid_ProgrameStart_Packet.param[4],17-4);
											
//											for(i = 4; i < 17;i++)
//											{
//												sum = sum + Grid_ProgrameStart_Packet.param[i];
//											}
											if(sum == Grid_ProgrameStart_Packet.data.sumvalue)
											{
										//		if(Grid_ProgrameStart_Packet.data.endByte == 0x2EE9C8FD)
									//		{
													bl_ctx.Updatapacketnum = 0;	
													bl_ctx.state = 0xc6;
													bl_ctx.framecount++;
													bl_ctx.fileID = Grid_ProgrameStart_Packet.data.fileID;
													bl_ctx.totalpacketnum = Grid_ProgrameStart_Packet.data.totalupdatenum[2]<<16
													+ Grid_ProgrameStart_Packet.data.totalupdatenum[1]<<8+Grid_ProgrameStart_Packet.data.totalupdatenum[0];
													bl_ctx.state = 0xc6;
				
													for(i=16;i<256;i++)
													{
													FLASH_EraseSector(FLASH_SECTOR_SIZE*i);
													FLASH_EraseVerifySection(FLASH_SECTOR_SIZE*i,128);
													}
													return kStatus_Success;
								//		}
											}
										}
									}
								}
							}
						}
							Grid_Response_Packet.data.startByte[0]  = 0x1A;
						  Grid_Response_Packet.data.startByte[1]  = 0xCF;
							Grid_Response_Packet.data.startByte[2]  = 0xFC;
							Grid_Response_Packet.data.startByte[3]  = 0x1D;						
							Grid_Response_Packet.data.lengthInBytes[0] = 0x00;
							Grid_Response_Packet.data.lengthInBytes[1] = 0x08;
							Grid_Response_Packet.data.destinationuser = PayLoad;
							Grid_Response_Packet.data.sourceuser = Grid;
							bl_ctx.framecount++;
						//	bl_ctx.framecount =  (bl_ctx.framecount&0XFF00)>>8 + (bl_ctx.framecount&0X00FF)<<8;
							Grid_Response_Packet.data.framecount[0] = (bl_ctx.framecount&0XFF00)>>8;
							Grid_Response_Packet.data.framecount[1] = (bl_ctx.framecount&0X00FF);
							Grid_Response_Packet.data.frameType = 0x99;
							Grid_Response_Packet.data.reponseType = 0X55;
							Grid_Response_Packet.data.versionnumber = bl_ctx.versionnumber;
							Grid_Response_Packet.data.fileID = bl_ctx.fileID;
							sum = 0;
							sum = 	XOR_Operation(&Grid_Response_Packet.param[4],14-4);
							Grid_Response_Packet.data.sumvalue = sum;
							Grid_Response_Packet.data.endByte[0]  = 0x2e;
							Grid_Response_Packet.data.endByte[1]  = 0xe9;
							Grid_Response_Packet.data.endByte[2]  = 0xc8;
							Grid_Response_Packet.data.endByte[3]  = 0xfd;
						//	Grid_Response_Packet.data.endByte = 0XFDC8E92E;
							bl_hw_if_write(Grid_Response_Packet.param, sizeof(Grid_Response_Packet.param));
						return kStatus_Fail;	
					break;
				case 0xc7:
						if(Packet_Length == 4129)
						{
						if(Grid_4096_Code_Packet.packet_data.startByte[0] == 0x1A
							&&Grid_4096_Code_Packet.packet_data.startByte[1] == 0xCF
						&&Grid_4096_Code_Packet.packet_data.startByte[2] == 0XFC
						&&Grid_4096_Code_Packet.packet_data.startByte[3] == 0X1D)
							{
								if(Grid_4096_Code_Packet.packet_data.lengthInBytes[0]*256+
									Grid_4096_Code_Packet.packet_data.lengthInBytes[1] == 4118)
								{
									if(Grid_4096_Code_Packet.packet_data.destinationuser == Grid)
									{
										if(Grid_4096_Code_Packet.packet_data.sourceuser == PayLoad)
										{
											if(Grid_4096_Code_Packet.packet_data.frameType == 0xc7)
											{		
												crcvalue = csp_crc32_memory(&receive_buffer[10],4110);
														if(crcvalue ==
															Grid_4096_Code_Packet.packet_data.crc32[0]*256*256*256+ Grid_4096_Code_Packet.packet_data.crc32[1]*256*256+
														Grid_4096_Code_Packet.packet_data.crc32[2]*256+Grid_4096_Code_Packet.packet_data.crc32[3])
														{
															sum = 0;
															sum = 	XOR_Operation(&receive_buffer[4],4124-4);
														
															if(sum == Grid_4096_Code_Packet.packet_data.checkvalue)
															{
																	grid_startaddress = (Grid_4096_Code_Packet.packet_data.startaddress[0]*256*256*256)+
																	(Grid_4096_Code_Packet.packet_data.startaddress[1]*256*256)+(Grid_4096_Code_Packet.packet_data.startaddress[2]*256)+
																(	Grid_4096_Code_Packet.packet_data.startaddress[3]);
			
																	grid_endaddress = (Grid_4096_Code_Packet.packet_data.endaddress[0]*256*256*256)+
																	(Grid_4096_Code_Packet.packet_data.endaddress[1]*256*256)+(Grid_4096_Code_Packet.packet_data.endaddress[2]*256)+
																	(Grid_4096_Code_Packet.packet_data.endaddress[3]);
																	if((grid_endaddress - grid_startaddress)== 4096)
																	{
																		
																			
																			bl_ctx.state = 0xc7;																
																			bl_ctx.code = 4096;
																	  //	flag_state = 	handle_flash_erase_region();
																			handle_write_memory();
																			status = handle_data_phase(&hasMoreData,&receive_buffer[24]);
																			if(status == kStatus_Success)
																			{
																				bl_ctx.Updatapacketnum ++;
																				//写入成功
																					Grid_Response_Packet.data.startByte[0]  = 0x1A;
																					Grid_Response_Packet.data.startByte[1]  = 0xCF;
																					Grid_Response_Packet.data.startByte[2]  = 0xFC;
																					Grid_Response_Packet.data.startByte[3]  = 0x1D;								
																					Grid_Response_Packet.data.lengthInBytes[0] = 0x00;
																					Grid_Response_Packet.data.lengthInBytes[1] = 0x08;
																					Grid_Response_Packet.data.destinationuser = PayLoad;
																					Grid_Response_Packet.data.sourceuser = Grid;
																					bl_ctx.framecount++;
																				//	bl_ctx.framecount =  (bl_ctx.framecount&0XFF00)>>8 + (bl_ctx.framecount&0X00FF)<<8;
																					Grid_Response_Packet.data.framecount[0] = (bl_ctx.framecount&0XFF00)>>8;
																					Grid_Response_Packet.data.framecount[1] = (bl_ctx.framecount&0X00FF);
																					Grid_Response_Packet.data.frameType = 0x98;
																					Grid_Response_Packet.data.reponseType = 0Xff;
																					Grid_Response_Packet.data.versionnumber = bl_ctx.versionnumber;
																					Grid_Response_Packet.data.fileID = bl_ctx.fileID;
																					sum = 0;
																					sum = 	XOR_Operation(&Grid_Response_Packet.param[4],14-4);
									
																					Grid_Response_Packet.data.sumvalue = sum;
																					Grid_Response_Packet.data.endByte[0]  = 0x2e;
																					Grid_Response_Packet.data.endByte[1]  = 0xe9;
																					Grid_Response_Packet.data.endByte[2]  = 0xc8;
																					Grid_Response_Packet.data.endByte[3]  = 0xfd;
																				//	Grid_Response_Packet.data.endByte = 0XFDC8E92E;
																					
																					bl_hw_if_write(Grid_Response_Packet.param, sizeof(Grid_Response_Packet.param));	

																			}
																			if ((status != kStatus_Success) || (hasMoreData))
																			{
																					Grid_Response_Packet.data.startByte[0]  = 0x1A;
																					Grid_Response_Packet.data.startByte[1]  = 0xCF;
																					Grid_Response_Packet.data.startByte[2]  = 0xFC;
																					Grid_Response_Packet.data.startByte[3]  = 0x1D;								
																					Grid_Response_Packet.data.lengthInBytes[0] = 0x00;
																					Grid_Response_Packet.data.lengthInBytes[1] = 0x08;
																					Grid_Response_Packet.data.destinationuser = PayLoad;
																					Grid_Response_Packet.data.sourceuser = Grid;
																					bl_ctx.framecount++;
																				//	bl_ctx.framecount =  (bl_ctx.framecount&0XFF00)>>8 + (bl_ctx.framecount&0X00FF)<<8;
																					Grid_Response_Packet.data.framecount[0] = (bl_ctx.framecount&0XFF00)>>8;
																					Grid_Response_Packet.data.framecount[1] = (bl_ctx.framecount&0X00FF);
																					Grid_Response_Packet.data.frameType = 0x98;
																					Grid_Response_Packet.data.reponseType = 0Xaa;
																					Grid_Response_Packet.data.versionnumber = bl_ctx.versionnumber;
																					Grid_Response_Packet.data.fileID = bl_ctx.fileID;
																					sum = 0;				
																					sum = 	XOR_Operation(&Grid_Response_Packet.param[4],14-4);
																					Grid_Response_Packet.data.sumvalue = sum;
																					Grid_Response_Packet.data.endByte[0]  = 0x2e;
																					Grid_Response_Packet.data.endByte[1]  = 0xe9;
																					Grid_Response_Packet.data.endByte[2]  = 0xc8;
																					Grid_Response_Packet.data.endByte[3]  = 0xfd;
																				//	Grid_Response_Packet.data.endByte = 0XFDC8E92E;
																					bl_hw_if_write(Grid_Response_Packet.param, sizeof(Grid_Response_Packet.param));	
																				//写入失败
																			}																								
																			
																			return kStatus_Success;																	
																	
																	}
																	
															}
														}
													}										
												}
											}
										}
									}
								
											Grid_Response_Packet.data.startByte[0]  = 0x1A;
											Grid_Response_Packet.data.startByte[1]  = 0xCF;
											Grid_Response_Packet.data.startByte[2]  = 0xFC;
											Grid_Response_Packet.data.startByte[3]  = 0x1D;						
									Grid_Response_Packet.data.lengthInBytes[0] = 0x00;
									Grid_Response_Packet.data.lengthInBytes[1] = 0x08;
									Grid_Response_Packet.data.destinationuser = PayLoad;
									Grid_Response_Packet.data.sourceuser = Grid;
									bl_ctx.framecount++;
								//	bl_ctx.framecount =  (bl_ctx.framecount&0XFF00)>>8 + (bl_ctx.framecount&0X00FF)<<8;
									Grid_Response_Packet.data.framecount[0] = (bl_ctx.framecount&0XFF00)>>8;
									Grid_Response_Packet.data.framecount[1] = (bl_ctx.framecount&0X00FF);
									Grid_Response_Packet.data.frameType = 0x98;
									Grid_Response_Packet.data.reponseType = 0X55;
									Grid_Response_Packet.data.versionnumber = bl_ctx.versionnumber;
									Grid_Response_Packet.data.fileID = bl_ctx.fileID;
							sum = 0;
							sum = 	XOR_Operation(&Grid_Response_Packet.param[4],14-4);
									
									Grid_Response_Packet.data.sumvalue = sum;
									Grid_Response_Packet.data.endByte[0]  = 0x2e;
									Grid_Response_Packet.data.endByte[1]  = 0xe9;
									Grid_Response_Packet.data.endByte[2]  = 0xc8;
									Grid_Response_Packet.data.endByte[3]  = 0xfd;
								//	Grid_Response_Packet.data.endByte = 0XFDC8E92E;
									bl_hw_if_write(Grid_Response_Packet.param, sizeof(Grid_Response_Packet.param));

									return kStatus_Fail;			
						}
					break;
				case 0xc8:
						if(Grid_SoftwareStart_Packet.data.startByte[0] == 0x1A
							&&Grid_SoftwareStart_Packet.data.startByte[1] == 0xCF
						&&Grid_SoftwareStart_Packet.data.startByte[2] == 0XFC&&Grid_SoftwareStart_Packet.data.startByte[3] == 0X1D)
						{
							if(Grid_SoftwareStart_Packet.data.lengthInBytes[1] == 8)
							{
								if(Grid_SoftwareStart_Packet.data.destinationuser == Grid)
								{
									if(Grid_SoftwareStart_Packet.data.sourceuser == PayLoad)
									{
										if(Grid_SoftwareStart_Packet.data.frameType == 0xc8)
										{				
																		sum = 0;
											sum = 	XOR_Operation(&Grid_SoftwareStart_Packet.param[4],14-4);
//											for(i = 4; i < 14;i++)
//											{
//												sum = sum + Grid_SoftwareStart_Packet.param[i];
//											}
											if(sum == Grid_SoftwareStart_Packet.data.sumvalue)
											{

													bl_ctx.state = 0xc8;
													return kStatus_Success;
											}
										}
									}
								}
							}
						}
											Grid_Response_Packet.data.startByte[0]  = 0x1A;
											Grid_Response_Packet.data.startByte[1]  = 0xCF;
											Grid_Response_Packet.data.startByte[2]  = 0xFC;
											Grid_Response_Packet.data.startByte[3]  = 0x1D;					
							Grid_Response_Packet.data.lengthInBytes[0] = 0x00;
							Grid_Response_Packet.data.lengthInBytes[1] = 0x08;
							Grid_Response_Packet.data.destinationuser = PayLoad;
							Grid_Response_Packet.data.sourceuser = Grid;
							bl_ctx.framecount++;
						//	bl_ctx.framecount =  (bl_ctx.framecount&0XFF00)>>8 + (bl_ctx.framecount&0X00FF)<<8;
							Grid_Response_Packet.data.framecount[0] = (bl_ctx.framecount&0XFF00)>>8;
							Grid_Response_Packet.data.framecount[1] = (bl_ctx.framecount&0X00FF);
							Grid_Response_Packet.data.frameType = 0x97;
							Grid_Response_Packet.data.reponseType = 0X55;
							Grid_Response_Packet.data.versionnumber = bl_ctx.versionnumber;
							Grid_Response_Packet.data.fileID = bl_ctx.fileID;
							sum = 0;
							sum = 	XOR_Operation(&Grid_Response_Packet.param[4],14-4);
//							for(i = 4; i < 14;i++)
//							{
//								sum = sum + Grid_Response_Packet.param[i];
//							}
							Grid_Response_Packet.data.sumvalue = sum;
							Grid_Response_Packet.data.endByte[0]  = 0x2e;
							Grid_Response_Packet.data.endByte[1]  = 0xe9;
							Grid_Response_Packet.data.endByte[2]  = 0xc8;
							Grid_Response_Packet.data.endByte[3]  = 0xfd;
						//	Grid_Response_Packet.data.endByte = 0XFDC8E92E;
							bl_hw_if_write(Grid_Response_Packet.param, sizeof(Grid_Response_Packet.param));
					return kStatus_Fail;							
					break;
			}		
			return kStatus_Fail;	
		
	}
		return kStatus_Busy;			
}

void Uart_Interrupt (UINT8 data)
{
	Uart_SendChar(data); /* Echos data that is received*/
}
//#define GPIO_PDIR_PDI_MASK                       0xFFFFFFFFu
//#define GPIO_PDIR_PDI_SHIFT                      0
//#define GPIO_PDIR_PDI(x)                         (((uint32_t)(((uint32_t)(x))<<GPIO_PDIR_PDI_SHIFT))&GPIO_PDIR_PDI_MASK)
void GPIO_PTI6_Init()
{
	GPIOC_BASE_PTR->PDDR &= ~(1 << 6);
	GPIOC_BASE_PTR->PIDR &=~ (1 << 6);
}
UINT8 Read_PTI6()
{
	UINT8 status = 0;
	status = ((GPIOC_BASE_PTR->PDIR)&(1<<6));
	return status;
}

int main(void)
{
		uint32_t i;
			uint32_t j;
		//Clk_Init();
	  init(); 			
    hardware_init();	
	  UART_Init();
		  GPIO_PTI6_Init();
		for(i = 0; i < 3000;i++);
   //if (stay_in_bootloader()||(Read_PTI6() ==  0x40))
		if((Read_PTI6() ==  0x40))
   {		
			for(j = 0; j < 20;j++)
		  for(i = 0; i < 5000;i++);
		  if((Read_PTI6() ==  0x40))
		 {
				for(j = 0; j < 20;j++)
				for(i = 0; i < 5000;i++);
				if((Read_PTI6() ==  0x40))
				{
					for(j = 0; j < 20;j++)
					for(i = 0; i < 5000;i++);
					if((Read_PTI6() ==  0x40))
					{
							 bootloader_run();
					}					
				}			 

		 }

   }
   else if((Read_PTI6() !=  0x40))
   {		 
			for(j = 0; j < 20;j++)
		  for(i = 0; i < 5000;i++);
		  if((Read_PTI6() !=  0x40))
		 {
				for(j = 0; j < 20;j++)
				for(i = 0; i < 5000;i++);
				if((Read_PTI6() !=  0x40))
				{
					for(j = 0; j < 20;j++)
					for(i = 0; i < 5000;i++);
					if((Read_PTI6() !=  0x40))
					{
						SCB->VTOR = ((uint32_t )((uint32_t *)0x2000));
						for(i = 0; i < 2000;i++);
						//SCB->VTOR = ((uint32_t )(0x2000));
						uint32_t *vectorTable = (uint32_t*)APPLICATION_BASE;
						uint32_t sp = vectorTable[0];
						uint32_t pc = vectorTable[1];
						application_run(sp, pc);
					}
				}
		 }
    }

    // Should never reach here.
    return 0;
}

#if BL_FEATURE_FLASH_SECURITY_DISABLE
    
#endif

bool is_valid_memory_range(uint32_t start, uint32_t length)
{
    bool isValid = true;
    if ((start < APPLICATION_BASE) || ((start + length) < APPLICATION_BASE) )
    {
        isValid = false;
    }
    
    return isValid;
}
void flash_init(void)
{
    uint32_t i;
    uint8_t *ram_func_start = (uint8_t*)&s_flash_ram_function[0];
    
    for(i=0; i<sizeof(s_flash_command_run); i++)
    {
        *ram_func_start++ = s_flash_command_run[i];
    }
    
    s_flash_run_entry = (flash_run_entry_t)((uint32_t)s_flash_ram_function + 1);
}

    
status_t flash_command_sequence(void)
{
    uint8_t fstat;
    status_t status = kStatus_Success;
    FTMRE_FSTAT = (FTFx_FSTAT_RDCOLERR_MASK | FTFx_FSTAT_ACCERR_MASK | FTFx_FSTAT_FPVIOL_MASK);
    
    __disable_irq();
    s_flash_run_entry(&FTMRE_FSTAT);
    __enable_irq();
    
    fstat = FTMRE_FSTAT;

    if (fstat & FTFx_FSTAT_ACCERR_MASK)
    {
        status = kStatus_FlashAccessError;
    }
    else if(fstat & FTFx_FSTAT_FPVIOL_MASK)
    {
        status = kStatus_FlashProtectionViolation;
    }
    else if (fstat & FTFx_FSTAT_MGSTAT0_MASK)
    {
        status = kStatus_FlashCommandFailure;
    }

    return status;
}

status_t flash_erase(uint32_t start, uint32_t length)
{
    uint32_t alignedStart;
    uint32_t alignedLength;
    status_t status = kStatus_Success;
    alignedStart = align_down(start, TARGET_FLASH_SECTOR_SIZE);
    alignedLength = align_up(start - alignedStart + length, TARGET_FLASH_SECTOR_SIZE);
    while(alignedLength)
    {
			  #if defined (FTMRE) 
           // Clear error flags
	         FTMRE_FSTAT = 0x30;
	
	         // Write index to specify the command code to be loaded
	         FTMRE_FCCOBIX = 0x0;
	         // Write command code and memory address bits[23:16]	
	         FTMRE_FCCOBHI = 0x0A;// EEPROM FLASH command
	         FTMRE_FCCOBLO = start>>16;// memory address bits[23:16]
	         // Write index to specify the lower byte memory address bits[15:0] to be loaded
	         FTMRE_FCCOBIX = 0x1;
	         // Write the lower byte memory address bits[15:0]
	         FTMRE_FCCOBLO = start;
	         FTMRE_FCCOBHI = start>>8;
			  #else 
          kFCCOBx[0] = alignedStart;
          FTMRE_FCCOBIX = FTFx_ERASE_SECTOR;			
			  #endif
        status = flash_command_sequence();
        if (status != kStatus_Success)
        {
            break;
        }
        alignedStart += TARGET_FLASH_SECTOR_SIZE;
        alignedLength -= TARGET_FLASH_SECTOR_SIZE;
    }

    return status;
}

#if BL_FEATURE_VERIFY
static status_t flash_verify_program(uint32_t start, const uint32_t *expectedData, uint32_t lengthInBytes)
{
    status_t status = kStatus_Success;
    while(lengthInBytes)
    {
        kFCCOBx[0] = start;
        FTFx->FCCOB0 = FTFx_PROGRAM_CHECK;
        FTFx->FCCOB4 = 1; // 0-Normal, 1-User, 2-Factory
        kFCCOBx[2] = *expectedData;
        
        status = flash_command_sequence();
        if (kStatus_Success != status)
        {
            break;
        }
        else
        {
            start += 4;
            expectedData++;
            lengthInBytes -= 4;
        }
    }
    return status;
}
#endif

static status_t flash_program(uint32_t start, uint32_t *src, uint32_t length)
{
    status_t status = kStatus_Success;
    uint8_t *byteSrcStart;
    uint32_t i;
#if BL_FEATURE_PROGRAM_PHASE
    uint8_t alignmentSize = 8;
#else
    uint8_t alignmentSize = 4;
#endif

#if BL_FEATURE_VERIFY
    uint32_t *compareSrc = (uint32_t*)src;
    uint32_t compareDst = start;
    uint32_t compareLength = align_up(length, alignmentSize);
#endif 
    
    if (start & (alignmentSize - 1))
    {
        status = kStatus_FlashAlignmentError;
    }
    else if(!is_valid_memory_range(start, length))
    {
        status = kStatusMemoryRangeInvalid;
    }
    else
    {
        while(length)
        {
            if (length < alignmentSize)
            {
                byteSrcStart = (uint8_t*)src;
                for(i=length; i<alignmentSize; i++)
                {
                    byteSrcStart[i] = 0xFF;
                }
            }
#if defined (FTMRE)
  FTMRE_FSTAT = 0x30;
		// Write index to specify the command code to be loaded
	FTMRE_FCCOBIX = 0x0;
	// Write command code and memory address bits[23:16]	
	FTMRE_FCCOBHI = 0x06;// program FLASH command
	FTMRE_FCCOBLO = start>>16;// memory address bits[23:16]
	// Write index to specify the lower byte memory address bits[15:0] to be loaded
	FTMRE_FCCOBIX = 0x1;
	// Write the lower byte memory address bits[15:0]
	FTMRE_FCCOBLO = start;
	FTMRE_FCCOBHI = start>>8;
	// Write index to specify the word0 (MSB word) to be programmed
	FTMRE_FCCOBIX = 0x2;
#if     defined(BIG_ENDIAN)        
	// Write the word  0
	FTMRE_FCCOBHI = (*src>>16)>>8;
	FTMRE_FCCOBLO = (*src>>16);
#else        
	FTMRE_FCCOBHI = (*src) >>8;	
	FTMRE_FCCOBLO = (*src);	
#endif        
	// Write index to specify the word1 (LSB word) to be programmed
	FTMRE_FCCOBIX = 0x3;
	// Write the word1 
#if     defined(BIG_ENDIAN)        
	FTMRE_FCCOBHI = (*src) >>8;	
	FTMRE_FCCOBLO = (*src);	
#else
	FTMRE_FCCOBHI = (*src>>16)>>8;
	FTMRE_FCCOBLO = (*src>>16);
#endif
src = src+1;
		
#else

            kFCCOBx[0] = start;
            kFCCOBx[1] = *src++;
#if BL_FEATURE_PROGRAM_PHASE
            kFCCOBx[2] = *src++;
#endif
#if BL_FEATURE_PROGRAM_PHASE
            FTFx->FCCOB0 = FTFx_PROGRAM_PHRASE;
#else
            FTMRE_FCCOBIX = FTFx_PROGRAM_LONGWORD;
#endif

#endif
            status = flash_command_sequence();
            if (status != kStatus_Success)
            {
                break;
            }
            start += alignmentSize;
            length -= (length > alignmentSize) ? alignmentSize: length;
        }
    }
    
#if BL_FEATURE_VERIFY  //zero, not used
    if (kStatus_Success == status)
    {
        status = flash_verify_program(compareDst, compareSrc, compareLength);
    }
#endif
    return status;
}

static status_t handle_flash_erase_region(void)
{
    status_t status = kStatus_Success;
    //flash_erase_region_packet_t *packet = (flash_erase_region_packet_t*)&s_readPacket.payload[0];

    uint32_t start = grid_startaddress;
    uint32_t length =grid_endaddress - grid_startaddress;
//		if(bl_ctx.code == 1024)
//		{
//			start = Grid_1024_Code_Packet.packet_data.startaddress;
//		  length =Grid_1024_Code_Packet.packet_data.endaddress - Grid_1024_Code_Packet.packet_data.startaddress;
//		}
    if (!is_valid_memory_range(start, length))
    {
        status = kStatusMemoryRangeInvalid; //start  和  length 不正确
    }
    else
    {
        status = flash_erase(start, length);
    }
		return status;
   // return send_generic_response(kCommandTag_FlashEraseRegion, status);
}

static status_t handle_write_memory(void)
{
   // write_memory_packet_t *packet = (write_memory_packet_t*)&s_readPacket.payload[0];

    bl_ctx.address = grid_startaddress;
    bl_ctx.count = grid_endaddress - grid_startaddress;
//		if(bl_ctx.code == 1024)
//		{
//			bl_ctx.address = Grid_1024_Code_Packet.packet_data.startaddress;
//			bl_ctx.count = Grid_1024_Code_Packet.packet_data.endaddress - Grid_1024_Code_Packet.packet_data.startaddress;		
//		}
  //  return send_generic_response(kCommandTag_WriteMemory, kStatus_Success);
	return 0;
}
static status_t handle_data_phase(bool *hasMoreData,uint8_t *data)
{
    uint16_t packetLength = grid_endaddress - grid_startaddress;
  //  uint32_t *src = (uint32_t*)&Grid_4096_Code_Packet.packet_data.payload;
//	 uint32_t *src = (uint32_t*)&receive_buffer[24];
		uint32_t *src = (uint32_t*)data;
    uint32_t writeLength;
    status_t status = kStatus_Success;
//		if(bl_ctx.code == 1024)
//		{
//			packetLength = Grid_4096_Code_Packet.packet_data.endaddress - Grid_4096_Code_Packet.packet_data.startaddress;
//			 src = (uint32_t*)&Grid_4096_Code_Packet.packet_data.payload;	
//		} 
    if(bl_ctx.count)
    {
        writeLength = (packetLength <= bl_ctx.count) ? packetLength : bl_ctx.count;
        {
            status = flash_program(bl_ctx.address, src, writeLength);
            if (status != kStatus_Success)
            {
                *hasMoreData = false;
                return status;
            }
        }
        bl_ctx.count -= writeLength;
        bl_ctx.address += writeLength;
    }
    if (bl_ctx.count)
    {
        *hasMoreData = true;
    }
    else
    {
        *hasMoreData = false;
    }
    return status;
}

void bootloader_run(void)
{
    status_t status;

    flash_init();
		uint32_t i; 
		uint8_t sum  =0 ;
    while(1)
    {
        // Read data from host
        status = serial_packet_read();
        if (status != kStatus_Success)
        {
            continue;
        }
            switch(bl_ctx.state)
            {
							case kFramingPacketType_Start:
						Grid_Response_Packet.data.startByte[0]  = 0x1A;
							Grid_Response_Packet.data.startByte[1]  = 0xCF;
							Grid_Response_Packet.data.startByte[2]  = 0xFC;
							Grid_Response_Packet.data.startByte[3]  = 0x1D;			
							Grid_Response_Packet.data.lengthInBytes[0] = 0x00;
							Grid_Response_Packet.data.lengthInBytes[1] = 0x08;
							Grid_Response_Packet.data.destinationuser = PayLoad;
							Grid_Response_Packet.data.sourceuser = Grid;
							bl_ctx.framecount++;
						//	bl_ctx.framecount =  (bl_ctx.framecount&0XFF00)>>8 + (bl_ctx.framecount&0X00FF)<<8;
							Grid_Response_Packet.data.framecount[0] = (bl_ctx.framecount&0XFF00)>>8;
							Grid_Response_Packet.data.framecount[1] = (bl_ctx.framecount&0X00FF);
							Grid_Response_Packet.data.frameType = 0x99;
							Grid_Response_Packet.data.reponseType = 0XFF;
							Grid_Response_Packet.data.versionnumber = bl_ctx.versionnumber;
							Grid_Response_Packet.data.fileID = bl_ctx.fileID;
							sum = 0;
							sum = 	XOR_Operation(&Grid_Response_Packet.param[4],14-4);
							Grid_Response_Packet.data.sumvalue = sum;
							Grid_Response_Packet.data.endByte[0]  = 0x2e;
							Grid_Response_Packet.data.endByte[1]  = 0xe9;
							Grid_Response_Packet.data.endByte[2]  = 0xc8;
							Grid_Response_Packet.data.endByte[3]  = 0xfd;
						//	Grid_Response_Packet.data.endByte = 0XFDC8E92E;
							bl_hw_if_write(Grid_Response_Packet.param, sizeof(Grid_Response_Packet.param));
							break;
							case 0XC8:
							Grid_Response_Packet.data.startByte[0]  = 0x1A;
							Grid_Response_Packet.data.startByte[1]  = 0xCF;
							Grid_Response_Packet.data.startByte[2]  = 0xFC;
							Grid_Response_Packet.data.startByte[3]  = 0x1D;						
							Grid_Response_Packet.data.lengthInBytes[0] = 0x00;
							Grid_Response_Packet.data.lengthInBytes[1] = 0x08;
							Grid_Response_Packet.data.destinationuser = PayLoad;
							Grid_Response_Packet.data.sourceuser = Grid;
							bl_ctx.framecount++;
						//	bl_ctx.framecount =  (bl_ctx.framecount&0XFF00)>>8 + (bl_ctx.framecount&0X00FF)<<8;
							Grid_Response_Packet.data.framecount[0] = (bl_ctx.framecount&0XFF00)>>8;
							Grid_Response_Packet.data.framecount[1] = (bl_ctx.framecount&0X00FF);
							Grid_Response_Packet.data.frameType = 0x97;
								Grid_Response_Packet.data.reponseType = 0XFF;
							Grid_Response_Packet.data.versionnumber = bl_ctx.versionnumber;
							Grid_Response_Packet.data.fileID = bl_ctx.fileID;
							sum = 0;
							sum = 	XOR_Operation(&Grid_Response_Packet.param[4],14-4);
							Grid_Response_Packet.data.sumvalue = sum;
							Grid_Response_Packet.data.endByte[0]  = 0x2e;
							Grid_Response_Packet.data.endByte[1]  = 0xe9;
							Grid_Response_Packet.data.endByte[2]  = 0xc8;
							Grid_Response_Packet.data.endByte[3]  = 0xfd;
						//	Grid_Response_Packet.data.endByte = 0XFDC8E92E;
							bl_hw_if_write(Grid_Response_Packet.param, sizeof(Grid_Response_Packet.param));
							for(i = 0; i < 5000;i++);
							NVIC_SystemReset();
									break;
						default:
							break;
        }
    }
}

void application_run(uint32_t sp, uint32_t pc)
{
    typedef void(*app_entry_t)(void);

    static uint32_t s_stackPointer = 0;
    static uint32_t s_applicationEntry = 0;
    static app_entry_t s_application = 0;
        SCB->VTOR = ((uint32_t )((uint32_t *)0x2000));
    s_stackPointer = sp;
    s_applicationEntry = pc;
    s_application = (app_entry_t)s_applicationEntry;

    // Change MSP and PSP
    __set_MSP(s_stackPointer);
    __set_PSP(s_stackPointer);

    // Jump to application
    s_application();

    // Should never reach here.
    __NOP();
}

void HardFault_Handler(void)
{
    NVIC_SystemReset();
    while(1)
    {
    }
}
