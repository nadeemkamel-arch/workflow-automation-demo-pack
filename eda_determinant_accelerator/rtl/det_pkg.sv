package det_pkg;
  parameter int DET_MAX_N = 4;
  parameter int DET_DATA_W = 16;
  parameter int DET_ACC_W = 64;

  typedef enum logic [3:0] {
    ST_IDLE,
    ST_LOAD,
    ST_BASE,
    ST_PIVOT,
    ST_FIND_SWAP,
    ST_SWAP,
    ST_ROW_SETUP,
    ST_COL_SETUP,
    ST_DIV_START,
    ST_DIV_WAIT,
    ST_ADVANCE,
    ST_DONE
  } det_state_t;
endpackage
