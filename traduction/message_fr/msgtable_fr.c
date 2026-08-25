/**
 * @file msgtable_fr.c
 * Main Message Table Jumptables (fr)
 *
 * Genere par tools/msg_build.py -- ne pas editer a la main.
 */

#include "sf33rd/Source/Game/message/fr/msgtable_fr.h"
#include "common.h"
#include "sf33rd/Source/Game/message/fr/pl00end_fr.h"
#include "sf33rd/Source/Game/message/fr/pl00tlk_fr.h"
#include "sf33rd/Source/Game/message/fr/pl00win_fr.h"
#include "sf33rd/Source/Game/message/fr/pl01end_fr.h"
#include "sf33rd/Source/Game/message/fr/pl01tlk_fr.h"
#include "sf33rd/Source/Game/message/fr/pl01win_fr.h"
#include "sf33rd/Source/Game/message/fr/pl02end_fr.h"
#include "sf33rd/Source/Game/message/fr/pl02tlk_fr.h"
#include "sf33rd/Source/Game/message/fr/pl02win_fr.h"
#include "sf33rd/Source/Game/message/fr/pl03end_fr.h"
#include "sf33rd/Source/Game/message/fr/pl03tlk_fr.h"
#include "sf33rd/Source/Game/message/fr/pl03win_fr.h"
#include "sf33rd/Source/Game/message/fr/pl04end_fr.h"
#include "sf33rd/Source/Game/message/fr/pl04tlk_fr.h"
#include "sf33rd/Source/Game/message/fr/pl04win_fr.h"
#include "sf33rd/Source/Game/message/fr/pl05end_fr.h"
#include "sf33rd/Source/Game/message/fr/pl05tlk_fr.h"
#include "sf33rd/Source/Game/message/fr/pl05win_fr.h"
#include "sf33rd/Source/Game/message/fr/pl06end_fr.h"
#include "sf33rd/Source/Game/message/fr/pl06tlk_fr.h"
#include "sf33rd/Source/Game/message/fr/pl06win_fr.h"
#include "sf33rd/Source/Game/message/fr/pl07end_fr.h"
#include "sf33rd/Source/Game/message/fr/pl07tlk_fr.h"
#include "sf33rd/Source/Game/message/fr/pl07win_fr.h"
#include "sf33rd/Source/Game/message/fr/pl08end_fr.h"
#include "sf33rd/Source/Game/message/fr/pl08tlk_fr.h"
#include "sf33rd/Source/Game/message/fr/pl08win_fr.h"
#include "sf33rd/Source/Game/message/fr/pl09end_fr.h"
#include "sf33rd/Source/Game/message/fr/pl09tlk_fr.h"
#include "sf33rd/Source/Game/message/fr/pl09win_fr.h"
#include "sf33rd/Source/Game/message/fr/pl10end_fr.h"
#include "sf33rd/Source/Game/message/fr/pl10tlk_fr.h"
#include "sf33rd/Source/Game/message/fr/pl10win_fr.h"
#include "sf33rd/Source/Game/message/fr/pl11end_fr.h"
#include "sf33rd/Source/Game/message/fr/pl11tlk_fr.h"
#include "sf33rd/Source/Game/message/fr/pl11win_fr.h"
#include "sf33rd/Source/Game/message/fr/pl12end_fr.h"
#include "sf33rd/Source/Game/message/fr/pl12tlk_fr.h"
#include "sf33rd/Source/Game/message/fr/pl12win_fr.h"
#include "sf33rd/Source/Game/message/fr/pl13end_fr.h"
#include "sf33rd/Source/Game/message/fr/pl13tlk_fr.h"
#include "sf33rd/Source/Game/message/fr/pl13win_fr.h"
#include "sf33rd/Source/Game/message/fr/pl14end_fr.h"
#include "sf33rd/Source/Game/message/fr/pl14win_fr.h"
#include "sf33rd/Source/Game/message/fr/pl15end_fr.h"
#include "sf33rd/Source/Game/message/fr/pl15tlk_fr.h"
#include "sf33rd/Source/Game/message/fr/pl15win_fr.h"
#include "sf33rd/Source/Game/message/fr/pl16end_fr.h"
#include "sf33rd/Source/Game/message/fr/pl16tlk_fr.h"
#include "sf33rd/Source/Game/message/fr/pl16win_fr.h"
#include "sf33rd/Source/Game/message/fr/pl17end_fr.h"
#include "sf33rd/Source/Game/message/fr/pl17win_fr.h"
#include "sf33rd/Source/Game/message/fr/pl18end_fr.h"
#include "sf33rd/Source/Game/message/fr/pl18tlk_fr.h"
#include "sf33rd/Source/Game/message/fr/pl18win_fr.h"
#include "sf33rd/Source/Game/message/fr/pl19end_fr.h"
#include "sf33rd/Source/Game/message/fr/pl19tlk_fr.h"
#include "sf33rd/Source/Game/message/fr/pl19win_fr.h"

MessageTable* pl_mes_tbl_fr[20] = {
    &pl00win_fr_tbl, &pl01win_fr_tbl, &pl02win_fr_tbl, &pl03win_fr_tbl,
    &pl04win_fr_tbl, &pl05win_fr_tbl, &pl06win_fr_tbl, &pl07win_fr_tbl,
    &pl08win_fr_tbl, &pl09win_fr_tbl, &pl10win_fr_tbl, &pl11win_fr_tbl,
    &pl12win_fr_tbl, &pl13win_fr_tbl, &pl14win_fr_tbl, &pl15win_fr_tbl,
    &pl16win_fr_tbl, &pl17win_fr_tbl, &pl18win_fr_tbl, &pl19win_fr_tbl,
};

MessageTable* pl_tlk_tbl_fr[20] = {
    &pl00tlk_fr_tbl, &pl01tlk_fr_tbl, &pl02tlk_fr_tbl, &pl03tlk_fr_tbl,
    &pl04tlk_fr_tbl, &pl05tlk_fr_tbl, &pl06tlk_fr_tbl, &pl07tlk_fr_tbl,
    &pl08tlk_fr_tbl, &pl09tlk_fr_tbl, &pl10tlk_fr_tbl, &pl11tlk_fr_tbl,
    &pl12tlk_fr_tbl, &pl13tlk_fr_tbl, &pl13tlk_fr_tbl, &pl15tlk_fr_tbl,
    &pl16tlk_fr_tbl, &pl16tlk_fr_tbl, &pl18tlk_fr_tbl, &pl19tlk_fr_tbl,
};

MessageTable* pl_end_tbl_fr[20] = {
    &pl00end_fr_tbl, &pl01end_fr_tbl, &pl02end_fr_tbl, &pl03end_fr_tbl,
    &pl04end_fr_tbl, &pl05end_fr_tbl, &pl06end_fr_tbl, &pl07end_fr_tbl,
    &pl08end_fr_tbl, &pl09end_fr_tbl, &pl10end_fr_tbl, &pl11end_fr_tbl,
    &pl12end_fr_tbl, &pl13end_fr_tbl, &pl14end_fr_tbl, &pl15end_fr_tbl,
    &pl16end_fr_tbl, &pl17end_fr_tbl, &pl18end_fr_tbl, &pl19end_fr_tbl,
};
