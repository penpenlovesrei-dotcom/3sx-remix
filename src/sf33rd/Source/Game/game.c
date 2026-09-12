#include "sf33rd/Source/Game/game.h"
#include "common.h"
#include "main.h"
#include "port/utils.h"
#include "port/video/jalon.h"
#include "sf33rd/AcrSDK/common/pad.h"
#include "sf33rd/Source/Common/PPGWork.h"
#include "sf33rd/Source/Game/debug/debug_config.h"
#include "sf33rd/Source/Game/demo/demo00.h"
#include "sf33rd/Source/Game/demo/demo01.h"
#include "sf33rd/Source/Game/demo/demo02.h"
#include "sf33rd/Source/Game/effect/eff35.h"
#include "sf33rd/Source/Game/effect/eff58.h"
#include "sf33rd/Source/Game/effect/effect.h"
#include "sf33rd/Source/Game/effect/effj2.h"
#include "sf33rd/Source/Game/ending/end_main.h"
#include "sf33rd/Source/Game/engine/bbbscom.h"
#include "sf33rd/Source/Game/engine/cmb_win.h"
#include "sf33rd/Source/Game/engine/grade.h"
#include "sf33rd/Source/Game/engine/hitcheck.h"
#include "sf33rd/Source/Game/engine/manage.h"
#include "sf33rd/Source/Game/engine/plcnt.h"
#include "sf33rd/Source/Game/engine/plcnt2.h"
#include "sf33rd/Source/Game/engine/plcnt3.h"
#include "sf33rd/Source/Game/engine/slowf.h"
#include "sf33rd/Source/Game/engine/spgauge.h"
#include "sf33rd/Source/Game/engine/stun.h"
#include "sf33rd/Source/Game/engine/vital.h"
#include "sf33rd/Source/Game/engine/workuser.h"
#include "sf33rd/Source/Game/io/gd3rd.h"
#include "sf33rd/Source/Game/io/pulpul.h"
#include "sf33rd/Source/Game/menu/menu.h"
#include "sf33rd/Source/Game/opening/op_sub.h"
#include "sf33rd/Source/Game/opening/opening.h"
#include "sf33rd/Source/Game/rendering/color3rd.h"
#include "sf33rd/Source/Game/rendering/dc_ghost.h"
#include "sf33rd/Source/Game/rendering/mmtmcnt.h"
#include "sf33rd/Source/Game/rendering/mtrans.h"
#include "sf33rd/Source/Game/rendering/texcash.h"
#include "sf33rd/Source/Game/screen/continue.h"
#include "sf33rd/Source/Game/screen/entry.h"
#include "sf33rd/Source/Game/screen/gameover.h"
#include "sf33rd/Source/Game/screen/next_cpu.h"
#include "sf33rd/Source/Game/screen/ranking.h"
#include "sf33rd/Source/Game/screen/sel_pl.h"
#include "sf33rd/Source/Game/screen/win.h"
#include "sf33rd/Source/Game/sound/se.h"
#include "sf33rd/Source/Game/sound/sound3rd.h"
#include "sf33rd/Source/Game/stage/bg.h"
#include "sf33rd/Source/Game/stage/bg_data.h"
#include "sf33rd/Source/Game/stage/bg_sub.h"
#include "sf33rd/Source/Game/stage/ta_sub.h"
#include "sf33rd/Source/Game/stage/tate00.h"
#include "sf33rd/Source/Game/system/reset.h"
#include "sf33rd/Source/Game/system/sys_sub.h"
#include "sf33rd/Source/Game/system/sys_sub2.h"
#include "sf33rd/Source/Game/system/sysdir.h"
#include "sf33rd/Source/Game/system/work_sys.h"
#include "sf33rd/Source/Game/ui/count.h"
#include "sf33rd/Source/Game/ui/flash_lp.h"
#include "sf33rd/Source/Game/ui/input_history.h"
#include "sf33rd/Source/Game/ui/sc_sub.h"
#include "sf33rd/Source/PS2/mc/savesub.h"
#include "structs.h"

void Wait_Auto_Load(struct _TASK* /* unused */);
void Loop_Demo(struct _TASK* /* unused */);
void Game();
void Game00();
void Game01();
void Game02();
void Game03();
void Game04();
void Game05();
void Game06();
void Game07();
void Game08();
void Game09();
void Game10();
void Game11();
void Game12();
void Check_Back_Demo();
void Game0_0();
void Game0_1();
void Game0_2();
void Next_Demo_Loop();
void Game12_0();
void Game12_1();
void Game12_2();
void Game2_0();
void Game2_1();
void Game2_2();
void Game2_3();
void Game2_4();
void Game2_5();
void Game2_6();
void Game2_7();
void Time_Control();
static s32 Check_Disp_Ranking();
s32 Disp_Ranking();
void Request_Break_Sub(s16 PL_id);
s16 Disp_Rank_Sub(s16 PL_id);
static s16 Bonus_Sub();
s16 Ck_Coin();
void Loop_Demo_Sub();
void Before_Select_Sub();

static void Set_Appear_Type_For_Mode() {
    appear_type = Is_Training_Mode(Mode_Type) ? APPEAR_TYPE_NON_ANIMATED : APPEAR_TYPE_ANIMATED;
}

void Game_Task(struct _TASK* task_ptr) {
    s16 ix;

    void (*Main_Jmp_Tbl[3])(struct _TASK*) = { Wait_Auto_Load, Loop_Demo, Game };

    if (!No_Trans) {
        init_color_trans_req();
    }

    Play_Game = 0;

    if (Game_pause != 0x81) {
        system_timer += 1;
    }

    Jalon("   init_texcash_before_process", 0);
    init_texcash_before_process();
    Jalon("   seqsBeforeProcess", 0);
    seqsBeforeProcess();

    if (nowSoftReset() == 0) {
        Jalon("   Main_Jmp_Tbl G_No[0] =", G_No[0]);
        Main_Jmp_Tbl[G_No[0]](task_ptr);
        Jalon("   Main_Jmp_Tbl rendue", 0);
    }

    Jalon("   seqsAfterProcess", 0);
    seqsAfterProcess();
    Jalon("   texture_cash_update", 0);
    texture_cash_update();
    Jalon("   move_pulpul_work", 0);
    move_pulpul_work();
    Jalon("   Check_LDREQ_Queue", 0);
    Check_LDREQ_Queue();
    Jalon("   Game_Task rendue", 0);
}

void Game() {
    void (*Game_Jmp_Tbl[13])() = { Game00, Game01, Game02, Game03, Game04, Game05, Game06,
                                   Game07, Game08, Game09, Game10, Game11, Game12 };

    if (G_No[1] == 2 || G_No[1] == 9) {
        Play_Game = 1;
    } else if (G_No[1] == 8) {
        Play_Game = 2;
    }

    Jalon("    Game_Jmp_Tbl G_No[1] =", G_No[1]);
    Game_Jmp_Tbl[G_No[1]]();
    Jalon("    Game_Jmp_Tbl rendue", 0);
}

void Game00() {
    void (*Game00_Jmp_Tbl[3])() = { Game0_0, Game0_1, Game0_2 };

    Game00_Jmp_Tbl[G_No[2]]();
    njSetBackColor(0, 0, 0);
    BG_Draw_System();
    Basic_Sub();
    Check_Back_Demo();
}

void Game0_0() {
    if (Title_At_a_Dash() != 0) {
        G_No[2] += 1;
    }
}

void Game0_1() {
    Disp_Copyright();
    TITLE_Move(1);

    if (Request_G_No) {
        G_No[2] += 1;
    }
}

void Game0_2() {
    switch (G_No[3]) {
    case 0:
        Disp_Copyright();
        TITLE_Move(1);
        G_No[3] += 1;
        Switch_Screen_Init(1);
        break;

    case 1:
        if (Switch_Screen(1) != 0) {
            G_No[3] += 1;
            Cover_Timer = 23;
            return;
        }

        TITLE_Move(1);
        Disp_Copyright();
        break;

    case 2:
        FadeOut(1, 0xFF, 8);
        G_No[3] += 1;
        break;

    case 3:
        FadeOut(1, 0xFF, 8);
        G_No[3] += 1;
        TexRelease(601);
        title_tex_flag = 0;
        break;

    case 4:
        FadeOut(1, 0xFF, 8);
        G_No[3] += 1;
        Purge_mmtm_area(2);
        Make_texcash_of_list(2);
        break;

    case 5:
        FadeOut(1, 0xFF, 8);
        BGM_Request(65);
        G_No[1] = 0xC;
        G_No[2] = 0;
        G_No[3] = 0;
        cpReadyTask(TASK_MENU, Menu_Task);
        break;
    }
}

void Check_Back_Demo() {
    if (++G_Timer < 1800) {
        return;
    }

    if (G_No[1] == 12 || (G_No[2] == 2 && G_No[3] >= 2)) {
        return;
    }

    TexRelease(601);
    title_tex_flag = 0;
    Next_Demo_Loop();
    effect_work_init();
}

/// Screen transition to character select
void Game12() {
    void (*Game12_Jmp_Tbl[3])() = { Game12_0, Game12_1, Game12_2 };

    Game12_Jmp_Tbl[G_No[2]]();
    BG_Draw_System();
    Basic_Sub();
    bg_pos_hosei_sub2(0);
    bg_pos_hosei_sub2(1);
    bg_pos_hosei_sub2(2);
    Bg_Family_Set_appoint(0);
    Bg_Family_Set_appoint(1);
    Bg_Family_Set_appoint(2);
    BG_move_Ex(0);
}

void Game12_0() {
    // Do nothing
}

void Game12_1() {
    G_No[2] += 1;
    Switch_Screen_Init(1);
    SsBgmFadeOut(0x1000);
}

void Game12_2() {
    if (!Switch_Screen(1)) {
        // Transition is still running, can't proceed
        return;
    }

    // Proceed to character select
    G_No[1] = 1;
    G_No[2] = 0;
    G_No[3] = 0;
    Control_Time = 481;
    Cover_Timer = 23;
    effect_work_init();
    cpExitTask(TASK_MENU);
}

/// Character select
void Game01() {
    BG_Draw_System();
    Basic_Sub();
    Setup_Play_Type();

    switch (G_No[2]) {
    case 0:
        Switch_Screen(1);
        G_No[2] += 1;
        S_No[0] = 0;
        S_No[1] = 0;
        S_No[2] = 0;
        S_No[3] = 0;
        SsBgmHalfVolume(0);

        if (Mode_Type == MODE_ARCADE) {
            BGM_Request(53);
        } else {
            BGM_Request(66);
        }

        Break_Into = 0;
        Stop_Combo = 0;

        if (Mode_Type != MODE_NETWORK) {
            Random_ix32 = Interrupt_Timer;
            Random_ix32_ex = Interrupt_Timer;
        } else {
            Setup_Net_Random_ix();
            All_Clear_Timer();
        }

        init_slow_flag();
        System_all_clear_Level_B();
        pulpul_stop();
        init_pulpul_work();
        break;

    case 1:
        Switch_Screen(1);
        G_No[2] += 1;
        break;

    case 2:
        if (Select_Player()) {
            G_No[2] += 1;
            Bonus_Game_Flag = 0;
            Switch_Screen_Init(0);
        }

        break;

    default:
        Select_Player();

        if (Switch_Screen(0) != 0) {
            Game01_Sub();
            Cover_Timer = 24;
            Set_Appear_Type_For_Mode();
            set_hitmark_color();

#if DEBUG
            if (debug_config.character_override[0]) {
                My_char[0] = debug_config.character_override[0] - 1;
            }

            if (debug_config.character_override[1]) {
                My_char[1] = debug_config.character_override[1] - 1;
            }
#endif

            Purge_texcash_of_list(3);
            Make_texcash_of_list(3);

            if (Demo_Flag) {
                // Straight to the stage, doing by hand the one thing Game05 would have done for
                // it. Game05 cannot be borrowed here: it opens with Basic_Sub, which draws every
                // effect still standing, and it is reached in an arcade run from a finished fight
                // whose texture list holds the menu charset. Arriving from a character select it
                // does not, and the renderer stops on a draw request for a multitexture that was
                // never brought up. Game09 opens with System_all_clear_Level_B instead, which
                // clears those works before anything is asked to draw.
                // Only the name and the route. Setup_Next_Fighter has already put Sean and the
                // bonus stage in place and asked for both, on the arcade's own path, so there is
                // nothing left here to load -- and asking again is what made every earlier attempt
                // fail, once as a duplicate transfer and once as a second stage over the first.
                if (Parry_The_Ball_Requested()) {
                    Bonus_Type = PARRY_THE_BALL_STAGE;
                }

                G_No[1] = Parry_The_Ball_Requested() ? 9 : 2;
                G_No[2] = 0;
                G_No[3] = 0;
                E_No[0] = 4;
                E_No[1] = 0;
                E_No[2] = 0;
                E_No[3] = 0;
            } else {
                Demo_Time_Stop = 1;
                plw[0].wu.operator = 0;
                Operator_Status[0] = 0;
                plw[1].wu.operator = 0;
                Operator_Status[1] = 0;
            }

            if (plw[0].wu.operator != 0) {
                Sel_Arts_Complete[0] = -1;
            }

            if (plw[1].wu.operator != 0) {
                Sel_Arts_Complete[1] = -1;
            }

            if ((plw[0].wu.operator != 0) && (plw[1].wu.operator != 0)) {
                Play_Type = 1;
            } else {
                Play_Type = 0;
            }
        }

        break;
    }

    BG_move();
}

void Game02() {
    void (*Game02_Jmp_Tbl[8])() = { Game2_0, Game2_1, Game2_2, Game2_3, Game2_4, Game2_5, Game2_6, Game2_7 };

    Scene_Cut = Cut_Cut_Cut();
    Jalon("     Game02_Jmp_Tbl G_No[2] =", G_No[2]);
    Game02_Jmp_Tbl[G_No[2]]();
    Jalon("     Game02_Jmp_Tbl rendue", 0);
    BG_move_Ex(3);
    Jalon("     BG_move_Ex rendu", 0);
}

void Game2_0() {
    s16 ix;

    BG_Draw_System();
    Switch_Screen(0);

    if (Check_LDREQ_Clear() == 0) {
        fatal_error("Load queue failed to drain in time");
    }

    System_all_clear_Level_B();

    switch (Mode_Type) {
    case MODE_ARCADE:
        Play_Mode = 0;
        Replay_Status[0] = 0;
        Replay_Status[1] = 0;
        break;

    case MODE_VERSUS:
        for (ix = 0; ix < 2; ix++) {
            if (save_w[1].Partner_Type[ix]) {
                plw[ix].wu.operator = 0;
                Operator_Status[ix] = 0;
            }
        }

        cpExitTask(TASK_ENTRY);
        /* fallthrough */

    case MODE_NETWORK:
        Play_Mode = 1;
        All_Clear_Random_ix();
        All_Clear_Timer();
        All_Clear_ETC();
        break;

    case MODE_REPLAY:
        Play_Mode = 3;
        All_Clear_Timer();
        break;

    default:
        // Do nothing
        break;
    }

    Check_Replay();

    if (Demo_Flag == 0) {
        Play_Mode = 0;
        Replay_Status[0] = 0;
        Replay_Status[1] = 0;
    }

    Game_difficulty = 15;
    Game_timer = 0;
    Game_pause = 0;
    Demo_Time_Stop = 0;
    C_No[0] = 0;
    C_No[1] = 0;
    C_No[2] = 0;
    C_No[3] = 0;
    G_No[2] = 3;
    G_Timer = 10;
    Round_num = 0;
    Keep_Grade[0] = 0;
    Keep_Grade[1] = 0;

    if (Win_Record[0]) {
        Keep_Grade[0] = grade_get_my_grade(0) + 1;
    }

    if (Win_Record[1]) {
        Keep_Grade[1] = grade_get_my_grade(1) + 1;
    }

    Allow_a_battle_f = 0;
    Time_in_Time = 60;
    init_slow_flag();
    clear_hit_queue();
    pcon_rno[0] = pcon_rno[1] = pcon_rno[2] = pcon_rno[3] = 0;
    ca_check_flag = 1;
    bg_work_clear();
    win_lose_work_clear();
    player_face_init();
    TATE00();
}

static bool should_render_input_history() {
    return Mode_Type == MODE_NORMAL_TRAINING && Training[0].contents[0][1][TRAINING_OPTION_INPUT_HISTORY];
}

/// Main gameplay routine
void Game2_1() {
    mpp_w.inGame = true;

    if (Game_pause != 0x81) {
        Game_timer += 1;
    }

    Jalon("      set_EXE_flag", 0);
    set_EXE_flag();
    Jalon("      ppgPurgeFromVRAM 5", 0);
    ppgPurgeFromVRAM(5);

    if (Disp_Cockpit) {
        Jalon("      Time_Control", 0);
        Time_Control();
    }

    Jalon("      Player_control", 0);
    Player_control();

    if (Disp_Cockpit) {
        Jalon("      vital_cont_main", 0);
        vital_cont_main();
        Jalon("      combo_cont_main", 0);
        combo_cont_main();
    }

    Jalon("      TATE00", 0);
    TATE00();
    Jalon("      Game_Management", 0);
    Game_Management();
    BG_Draw_System();
    Jalon("      ppgPurgeFromVRAM 4", 0);
    ppgPurgeFromVRAM(4);
    Jalon("      reqPlayerDraw", 0);
    reqPlayerDraw();
    Jalon("      Basic_Sub_Ex", 0);
    Basic_Sub_Ex();

    if (Disp_Cockpit) {
        Jalon("      player_face", 0);
        player_face();
        Jalon("      player_name", 0);
        player_name();
        Jalon("      stngauge_cont_main", 0);
        stngauge_cont_main();
        Jalon("      spgauge_cont_main", 0);
        spgauge_cont_main();
        Jalon("      Sa_frame_Write", 0);
        Sa_frame_Write();
        Jalon("      Score_Sub", 0);
        Score_Sub();
        Jalon("      Flash_Lamp", 0);
        Flash_Lamp();
        Jalon("      Disp_Win_Record", 0);
        Disp_Win_Record();

        if (should_render_input_history()) {
            Jalon("      InputHistory_Render", 0);
            InputHistory_Render();
        }
    }

    Jalon("      ppgPurgeFromVRAM 0", 0);
    ppgPurgeFromVRAM(0);
    Jalon("      hit_check_main_process", 0);
    hit_check_main_process();
    Jalon("      Game2_1 rendue", 0);
}

void Game2_2() {
    s16 i;

    BG_Draw_System();
    Switch_Screen(0);

    if (Check_LDREQ_Clear() == 0) {
        fatal_error("Load queue failed to drain in time");
    }

    SsBgmHalfVolume(0);
    All_Clear_Timer();
    Check_Replay();
    Game_difficulty = 15;
    Game_timer = 0;
    Game_pause = 0;
    Demo_Time_Stop = 0;
    C_No[0] = 0;
    C_No[1] = 0;
    C_No[2] = 0;
    C_No[3] = 0;
    G_Timer = 10;
    Round_num = 0;
    Keep_Grade[0] = 0;
    Keep_Grade[1] = 0;

    if (Win_Record[0]) {
        Keep_Grade[0] = grade_get_my_grade(0) + 1;
    }

    if (Win_Record[1]) {
        Keep_Grade[1] = grade_get_my_grade(1) + 1;
    }

    Allow_a_battle_f = 0;
    Time_in_Time = 60;
    init_slow_flag();
    effect_work_quick_init();
    clear_hit_queue();
    pcon_rno[0] = pcon_rno[1] = pcon_rno[2] = pcon_rno[3] = 0;
    ca_check_flag = 1;
    bg_work_clear();
    win_lose_work_clear();
    player_face_init();
    Game01_Sub();
    Set_Appear_Type_For_Mode();
    TATE00();

    /* Quatre et non trois : c'est ici que les plans sont rallumes au debut du combat,
       en double de `Bg_Texture_Load_EX`. Le quatrieme plan des etages ajoutes restait
       eteint parce que cette boucle-ci s'arretait a trois -- le decor etait charge mais
       jamais dessine. */
    for (i = 0; i < 4; i++) {
        if (stage_bgw_number[bg_w.stage][i] > 0) {
            Bg_On_R(1 << i);
        }
    }

    if (bg_w.stage == 7) {
        Bg_On_R(4);
    }

    G_No[2] = 7;
}

void Game2_3() { // 🟢
    Game2_1();

    if (--G_Timer == 0) {
        G_No[2] = 1;
        Clear_Flash_No();
    }
}

void Game2_4() {
    BG_Draw_System();
}

/// Rounds 2, 3, ... routine
void Game2_5() {
    BG_Draw_System();

    switch (G_No[3]) {
    case 0:
        Switch_Screen(0);
        G_No[3] += 1;
        Stop_Update_Score = 0;
        HUD_Shift_Init();
        vital_cont_init();
        count_cont_init(0);
        stngauge_cont_init();
        stngauge_work_clear();
        combo_cont_init();
        count_cont_init(1);
        Score[0][2] = 0;
        Score[1][2] = 0;
        Suicide[0] = 1;
        Game_pause = 0;
        pcon_rno[0] = 0;
        pcon_rno[1] = 0;
        pcon_rno[2] = 0;
        pcon_rno[3] = 0;
        appear_type = APPEAR_TYPE_NON_ANIMATED;
        erase_extra_plef_work();
        compel_bg_init_position();
        win_lose_work_clear();
        TATE00();
        break;

    default:
        Game2_1();

        if (--G_Timer == 0) {
            G_No[2] = 1;
            Clear_Flash_No();
        }

        break;
    }
}

void Game2_6() {
    BG_Draw_System();
    Switch_Screen(0);

    if (Wait_Seek_Time() != 0) {
        G_No[2] = 3;
        TATE00();
    }
}

void Game2_7() {
    BG_Draw_System();
    Switch_Screen(0);

    if (Wait_Seek_Time() != 0) {
        G_No[2] = 3;
    }
}

void Game01_Sub() {
    Disp_Cockpit = 0;
    Stop_Update_Score = 0;
    HUD_Shift_Init();
    vital_cont_init();
    count_cont_init(0);
    Score[0][1] = 0;
    Score[0][2] = 0;
    Score[1][1] = 0;
    Score[1][2] = 0;
    PL_Wins[0] = 0;
    PL_Wins[1] = 0;
    combo_cont_init();
    Clear_Win_Type();
    Lamp_No = 0;
    set_kizetsu_status(0);
    set_kizetsu_status(1);
    set_super_arts_status(0);
    set_super_arts_status(1);

    if (Demo_Flag && (sag_ikinari_max() != 0)) {
        spgauge_cont_init();
    } else {
        spgauge_cont_demo_init();
    }

    stngauge_cont_init();
}

void Game03() {
    BG_Draw_System();
    move_effect_work(4);
    move_effect_work(5);
    Play_Mode = 0;
    Replay_Status[0] = 0;
    Replay_Status[1] = 0;

    switch (G_No[2]) {
    case 0:
        if (!Winner_Scene()) {
            break;
        }

        switch (Mode_Type) {
        case MODE_VERSUS:
        case MODE_NETWORK:
            G_No[2] += 1;
            Rep_Game_Infor[10].play_type = 1;
            Rep_Game_Infor[10].winner = Winner_id;
            Switch_Screen_Init(0);

            if (Country == 3) {
                Rep_Game_Infor[10].play_type = 4;
            }

            break;

            // case MODE_NETWORK:
            // G_No[2] = 3;
            // Rep_Game_Infor[10].play_type = 2;
            // Rep_Game_Infor[10].winner = Winner_id;
            // Champion = Winner_id;
            // New_Challenger = Loser_id;
            // Switch_Screen_Init(0);
            // break;

        case MODE_REPLAY:
            G_No[2] = 5;
            cpReadyTask(TASK_MENU, Menu_Task);
            task[TASK_MENU].r_no[0] = 8;
            break;

        default:
            G_No[1] = 5;
            G_No[2] = 0;
            G_No[3] = 0;
            E_No[0] = 9;
            E_No[1] = 0;
            E_No[2] = 0;
            E_No[3] = 0;

            if (Battle_Q[WINNER]) {
                G_No[1] = 11;
                G_No[2] = 3;
                G_No[3] = 0;
            }

            Cover_Timer = 24;

            if (Round_Operator[LOSER]) {
                E_Number[LOSER][0] = 1;
                E_Number[LOSER][1] = 0;
                E_Number[LOSER][2] = 0;
                E_Number[LOSER][3] = 0;
            }

            break;
        }

        break;

    case 1:
        if (!Switch_Screen(1)) {
            break;
        }

        G_No[2] += 1;
        E_No[0] = 1;
        E_No[1] = 2;
        E_No[2] = 2;
        E_No[3] = 0;
        Request_E_No = 0;
        cpReadyTask(TASK_MENU, Menu_Task);
        task[TASK_MENU].r_no[1] = 16;
        Cursor_Y_Pos[0][0] = 0;
        Cursor_Y_Pos[1][0] = 0;
        G_Timer = 4;
        break;

    case 2:
        Switch_Screen(1);

        if (--G_Timer) {
            break;
        }

        Cover_Timer = 10;
        G_No[1] = 12;
        G_No[2] = 0;
        G_No[3] = 0;

        break;

    case 3:
        if (!Switch_Screen(1)) {
            break;
        }

        G_No[2] += 1;
        task[7].r_no[0] = 1;
        G_Timer = 4;
        break;

    case 4:
        Switch_Screen(1);

        if (--G_Timer) {
            break;
        }

        // Do nothing
        break;

    case 5:
        // Do nothing
        break;
    }

    BG_move();
}

void Game04() {
    s16 i;

    BG_Draw_System();
    move_effect_work(4);
    move_effect_work(5);

    switch (G_No[2]) {
    case 0:
        if (Loser_Scene() != 0) {
            if (Mode_Type == 5) {
                G_No[2] = 5;
                cpReadyTask(TASK_MENU, Menu_Task);
                task[TASK_MENU].r_no[0] = 8;
            } else {
                G_No[1] = 7;
                G_No[2] = 0;
                G_No[3] = 0;
                E_No[0] = 7;
                Cont_No[0] = 0;
                E_Number[LOSER][0] = 1;

                for (i = 1; i < 4; i++) {
                    E_No[i] = 0;
                    Cont_No[i] = 0;
                    E_Number[LOSER][i] = 0;
                }
            }
        }

        break;

    default:
        // Do nothing
        break;
    }

    BG_move();
}

void Game05() {
    BG_Draw_System();
    Basic_Sub();
    Setup_Play_Type();

    switch (G_No[2]) {
    case 0:
        G_No[2] += 1;
        SC_No[0] = 0;
        SC_No[1] = 0;
        SC_No[2] = 0;
        SC_No[3] = 0;

        if (Check_Bonus_Stage()) {
            SC_No[0] = 6;
        }

        Stop_Combo = 0;
        init_slow_flag();
        pulpul_stop();
        break;

    case 1:
        if (Next_CPU()) {
            G_No[2] += 1;
            Switch_Screen_Init(0);
        }

        break;

    default:
        Next_CPU();

        if (Switch_Screen(0) != 0) {
            Cover_Timer = 24;
            Purge_texcash_of_list(3);
            Make_texcash_of_list(3);

            if (Bonus_Type == 0) {
                Game01_Sub();
            }

            BGM_Stop();

            if (Bonus_Type == 0) {
                G_No[1] = 2;
                G_No[2] = 0;
                E_No[0] = 4;
                E_No[1] = 0;
                E_No[2] = 0;
                E_No[3] = 0;
                Bonus_Game_Flag = 0;
            } else {
                G_No[1] = 9;
                G_No[2] = 0;
                G_No[3] = 0;
                E_No[0] = 4;
                E_No[1] = 0;
                E_No[2] = 0;
                E_No[3] = 0;
            }
        }

        break;
    }

    BG_move();
}

void Game06() {
    s16 xx;

    BG_Draw_System();
    Basic_Sub_Ex();

    if (!Break_Into) {
        switch (G_No[2]) {
        case 0:
            G_No[2] += 1;
            Game_pause = 0;
            Stock_Com_Color[Player_id] = -1;
            Stock_Com_Arts[Player_id] = -1;
            Last_Player_id = -1;
            Control_Time = 481;
            E_No[0] = 8;
            E_No[1] = 0;
            E_No[2] = 0;
            E_No[3] = 0;

            for (xx = 0; xx < 4; xx++) {
                GO_No[xx] = 0;
            }

            make_texcash_work(13);
            break;

        case 1:
            if (Game_Over()) {
                G_Timer = 60;

                if (Check_Disp_Ranking() != 0) {
                    G_No[2] += 1;
                } else {
                    G_No[2] = 3;
                }
            }

            break;

        case 2:
            if (Disp_Ranking() != 0) {
                G_No[2] += 1;
                G_Timer = 1;
            }

            break;

        case 3:
            if (--G_Timer == 0) {
                G_No[2] += 1;
                Clear_Disp_Ranking(0);
                Clear_Disp_Ranking(1);
                Switch_Screen_Init(1);
            }

            break;

        case 4:
            if (Switch_Screen(1) != 0) {
                Cover_Timer = 24;
                Forbid_Break = 0;
                Clear_Flash_No();
                Clear_Personal_Data(LOSER);
                grade_check_work_1st_init(LOSER, 0);
                grade_check_work_1st_init(LOSER, 1);

                if (Request_Break[0] != 0 || Request_Break[1] != 0) {
                    Request_Break_Sub(0);
                    Request_Break_Sub(1);
                    G_No[1] = 1;
                    G_No[2] = 0;
                    G_No[3] = 0;
                    E_No[0] = 2;
                    E_No[1] = 0;
                    E_No[2] = 0;
                    E_No[3] = 0;
                    break;
                }

                for (xx = 0; xx < 20; xx++) {
                    save_w[Present_Mode].Ranking[xx] = Ranking_Data[xx];
                }

                G_No[2] = 5;
                G_No[3] = 0;
                G_Timer = 4;
                Pause_ID = Player_id;
                System_all_clear_Level_B();
                Forbid_Reset = 1;
                Copy_Check_w();
                cpExitTask(TASK_SAVER);
            }

            break;

        case 5:
            if (G_No[3] == 0) {
                FadeOut(1, 0xFF, 8);

                if (--G_Timer == 0) {
                    G_No[3] = 1;
                    SaveInit(SAVE_FILE_SETTINGS, SAVE_MODE_SAVE);
                }
            } else if (SaveMove() <= 0) {
                Forbid_Reset = 0;
                G_No[2] = 6;
            }

            break;

        case 6:
            Switch_Screen(1);
            G_No[0] = 1;
            G_No[1] = 0x63;
            G_No[2] = 0;
            G_No[3] = 0;
            E_No[0] = 0;
            E_No[1] = 0x63;
            E_No[2] = 0;
            E_No[3] = 0;
            D_No[0] = 0;
            D_No[1] = 0;
            D_No[2] = 0;
            D_No[3] = 0;
            Get_Demo_Index = 0;
            Combo_Demo_Flag = 0;
            cpReadyTask(TASK_ENTRY, Entry_Task);
            Purge_mmtm_area(5);
            Make_texcash_of_list(5);
            System_all_clear_Level_B();
            break;
        }

        BG_move();
    }
}

void Request_Break_Sub(s16 PL_id) {
    if ((Request_Break[PL_id] != 0) && (Ck_Break_Into(0, 0, PL_id) != 0)) {
        plw[PL_id].wu.operator = 1;
        Operator_Status[PL_id] = 1;
    }
}

s32 Check_Disp_Ranking() {
    s16 rank_type = Disp_Rank_Sub(0);

    if (rank_type != -1) {
        Rank_Type = rank_type;
        Present_Rank[0] = Rank_In[0][rank_type];
        Present_Rank[1] = Rank_In[1][rank_type];
        return 1;
    }

    rank_type = Disp_Rank_Sub(1);

    if (rank_type != -1) {
        Rank_Type = rank_type;
        Present_Rank[1] = Rank_In[1][rank_type];
        return 1;
    }

    return 0;
}

s16 Disp_Rank_Sub(s16 PL_id) {
    if (Request_Disp_Rank[PL_id][3] >= 0) {
        return 15;
    }

    if (Request_Disp_Rank[PL_id][2] >= 0) {
        return 10;
    }

    if (Request_Disp_Rank[PL_id][1] >= 0) {
        return 5;
    }

    if (Request_Disp_Rank[PL_id][0] >= 0) {
        return 0;
    }

    return -1;
}

s32 Disp_Ranking() {
    switch (G_No[3]) {
    case 0:
        G_No[3] += 1;
        Switch_Screen_Init(1);
        BGM_Request(57);
        break;

    case 1:
        if (Switch_Screen(1) != 0) {
            Cover_Timer = 24;
            G_No[3] += 1;
            D_No[0] = 1;
            D_No[1] = 0;
            D_No[2] = 0;
            D_No[3] = 0;
            Clear_Personal_Data(0);
            grade_check_work_1st_init(0, 0);
            grade_check_work_1st_init(0, 1);
            Clear_Personal_Data(1);
            grade_check_work_1st_init(1, 0);
            grade_check_work_1st_init(1, 1);
        }

        break;

    case 2:
        Switch_Screen(1);
        Ranking();

        if (--Cover_Timer == 0) {
            G_No[3] += 1;
            Switch_Screen_Init(1);
        }

        break;

    case 3:
        Ranking();

        if (Switch_Screen_Revival(1) != 0) {
            G_No[3] += 1;
            Forbid_Break = 0;
        }

        break;

    default:
        if (Ranking() != 0) {
            BGM_Stop();
            return 1;
        }

        break;
    }

    return 0;
}

void Game07() {
    BG_Draw_System();
    Basic_Sub();

    switch (G_No[2]) {
    case 0:
        if (Continue_Scene() != 0) {
            G_No[1] = 6;
            G_No[2] = 0;
        }

        break;
    }

    BG_move();
}

void Game08() {
    BG_Draw_System();

    switch (G_No[2]) {
    case 0:
        Switch_Screen(0);
        G_No[2] = 1;
        Game_pause = 0;
        Final_Result_id = WINNER;
        WGJ_Target = WINNER;
        WGJ_Win = Win_Record[WINNER];
        grade_final_grade_bonus();
        WGJ_Score = Continue_Coin[WINNER] + Score[WINNER][0];
        Purge_mmtm_area(6);
        cpExitTask(TASK_MENU);
        cpExitTask(TASK_PAUSE);
        break;

    case 1:
        if (Ending_main(End_PL) && (Request_Fade(9) != 0)) {
            G_No[2] += 1;
        }

        break;

    case 2:
        if (Check_Fade_Complete_SP() != 0) {
            G_No[2] += 1;
            G_Timer = 10;
            Suicide[4] = 1;
        }

        break;

    case 3:
        if (--G_Timer == 0) {
            G_No[1] = 6;
            G_No[2] = 0;
            E_No[0] = 8;
            E_No[1] = 0;
            E_No[2] = 0;
            E_No[3] = 0;
            Clear_Personal_Data(0);
            Clear_Personal_Data(1);
            plw[0].wu.operator = 0;
            plw[1].wu.operator = 0;
            Operator_Status[0] = 0;
            Operator_Status[1] = 0;
            Last_Player_id = Player_Number = -1;
            Purge_mmtm_area(6);
            System_all_clear_Level_B();
        }

        break;
    }

    move_effect_work(4);
}

/// @name The menu that ends PARRY THE BALL
///
/// A stage asked for by name has nowhere to hand back to: nobody started a run, so carrying on
/// into one is not a continuation but a non sequitur. It stops on a menu instead.
///
/// Drawn with SSPutStr rather than the menus' own machinery, for the same reason the palette lines
/// on the character select are: it needs no charset brought up and no effect work, so it can be
/// put on screen from inside the game task without anything being loaded for it.
/// @{
#define BALL_MENU_ROWS 3
#define BALL_MENU_RETRY 0
#define BALL_MENU_LEVEL 1
#define BALL_MENU_EXIT 2
/// Cell columns and rows of the 384x224 picture, SSPutStr counting in eights
#define BALL_MENU_X 16
#define BALL_MENU_Y 14
#define BALL_MENU_STEP 2
/// The blue bank the PRESS START lines use
#define BALL_MENU_ATTR 9
/// PrioBase[1], the layer that goes in front of a running stage. Not the HUD's own 2, which is
/// where this menu spent its first four attempts being drawn behind the scene -- SSPutStr2, the
/// one pause.c uses over gameplay, is SSPutStr with this priority hard-coded and nothing else
/// different.
#define BALL_MENU_PRIORITY 1
#define BALL_MENU_LIT 0xFFFFFFFF
#define BALL_MENU_DIM 0xFF707070

static s16 ball_menu_row;

static const s8* const ball_menu_label[BALL_MENU_ROWS] = { "RETRY", "LEVEL", "EXIT" };

/// @brief The three rows, and the level beside the middle one.
///
/// Redrawn every frame, which is what SSPutStr expects: it pushes quads rather than leaving
/// anything standing.
static void Ball_Menu_Draw() {
    s16 i;

    for (i = 0; i < BALL_MENU_ROWS; i++) {
        const u32 col = (i == ball_menu_row) ? BALL_MENU_LIT : BALL_MENU_DIM;

        SSPutStrCol(BALL_MENU_X, BALL_MENU_Y + i * BALL_MENU_STEP, BALL_MENU_ATTR, col, ball_menu_label[i],
                    BALL_MENU_PRIORITY);
    }

    {
        // Two digits so the row does not shuffle as the number crosses ten, and one past the label
        // so the two read as a pair. The level is one-based on screen and zero-based underneath,
        // which is the numbering set_bonus_game_nando already uses.
        const s16 shown = (s16)(Parry_The_Ball_Level() + 1);
        s8 text[4];

        text[0] = (s8)('0' + (shown / 10));
        text[1] = (s8)('0' + (shown % 10));
        text[2] = 0;

        SSPutStrCol(BALL_MENU_X + 7, BALL_MENU_Y + BALL_MENU_LEVEL * BALL_MENU_STEP, BALL_MENU_ATTR,
                    (ball_menu_row == BALL_MENU_LEVEL) ? BALL_MENU_LIT : BALL_MENU_DIM, text, BALL_MENU_PRIORITY);
    }
}

/// What Ball_Menu_Move answers
#define BALL_MENU_CHOSE_NOTHING 0
#define BALL_MENU_CHOSE_AGAIN 1
#define BALL_MENU_CHOSE_EXIT 2

/// @return One of BALL_MENU_CHOSE_*.
static s32 Ball_Menu_Move() {
    const u16 edge = (u16)(~p1sw_1 & p1sw_0);

    Ball_Menu_Draw();

    if (edge & SWK_UP) {
        ball_menu_row = (s16)((ball_menu_row + BALL_MENU_ROWS - 1) % BALL_MENU_ROWS);
        SE_dir_cursor_move();
    } else if (edge & SWK_DOWN) {
        ball_menu_row = (s16)((ball_menu_row + 1) % BALL_MENU_ROWS);
        SE_dir_cursor_move();
    } else if ((ball_menu_row == BALL_MENU_LEVEL) && (edge & (SWK_LEFT | SWK_RIGHT))) {
        Parry_The_Ball_Step_Level((edge & SWK_LEFT) ? -1 : 1);
        SE_dir_cursor_move();
    }

    if (!(edge & SWK_ATTACKS)) {
        return BALL_MENU_CHOSE_NOTHING;
    }

    SE_selected();

    // LEVEL is changed with left and right like any value row, so confirming on it starts the
    // stage at what it now says rather than needing a trip up to RETRY.
    if (ball_menu_row != BALL_MENU_EXIT) {
        Parry_The_Ball_Again();
        return BALL_MENU_CHOSE_AGAIN;
    }

    return BALL_MENU_CHOSE_EXIT;
}
/// @}

void Game09() {
    switch (G_No[2]) {
    case 0:
        BG_Draw_System();
        Switch_Screen(0);
        System_all_clear_Level_B();
        Bonus_Game_Flag = Bonus_Type;
        Game_difficulty = 15;
        Game_timer = 0;
        Game_pause = 0;
        Demo_Time_Stop = 0;
        C_No[0] = 0;
        C_No[1] = 0;
        C_No[2] = 0;
        C_No[3] = 0;
        G_No[2] += 1;
        G_Timer = 19;
        Round_num = 0;
        Allow_a_battle_f = 0;
        Time_in_Time = 60;
        init_slow_flag();
        clear_hit_queue();
        pcon_rno[0] = pcon_rno[1] = pcon_rno[2] = pcon_rno[3] = 0;
        bbbs_com_initialize();
        ca_check_flag = 1;
        Bonus_Game_Work = 20;
        Bonus_Game_result = 0;
        Bonus_Game_ex_result = 0;
        bg_work_clear();
        win_lose_work_clear();

        if (Bonus_Game_Flag == 0x15) {
            My_char[COM_id] = 12;
        } else {
            My_char[COM_id] = My_char[Player_id];
        }

        break;

    case 1:
        BG_Draw_System();
        Switch_Screen(1);

        if (--G_Timer == 0) {
            if (!Check_LDREQ_Queue_BG(bg_w.stage)) {
                G_Timer = 1;
            } else {
                G_No[2] += 1;
                Clear_Flash_No();

                if (Bonus_Type == 0x15) {
                    makeup_bonus_game_level(COM_id);
                    // Consumed here rather than where it was read: the level is only settled on
                    // this line, and a request left armed would send the next fight back to the
                    // bonus stage for as long as the session lasted.
                    Parry_The_Ball_Clear();
                    effect_35_init(0x3C, 5);
                    effect_J2_init(0x78);
                    effect_35_init(0xB4, 7);
                    effect_58_init(6, 0xB4, 0xA1);
                } else {
                    effect_35_init(0x3C, 6);
                    effect_35_init(0x78, 7);
                    effect_58_init(6, 0x78, 0xA1);
                }


                TATE00();
                Switch_Screen_Init(0);
                Bonus_Sub();
            }
        }

        break;

    case 2:
        Bonus_Sub();

        if (Switch_Screen_Revival(1) != 0) {
            G_No[2] += 1;
            Forbid_Break = 0;
        }

        break;

    case 3:
        // The menu is up: the stage is over and frozen, and nothing else here runs again until one
        // of its rows says so. G_No[3] carries that, this case being the only one that touches it.
        if (G_No[3] != 0) {
            const s16 chosen = Ball_Menu_Move();

            if (chosen == BALL_MENU_CHOSE_AGAIN) {
                // Nothing to tear down by hand: case 0 opens with System_all_clear_Level_B, which
                // is the very teardown this state was put in front of.
                G_No[2] = 0;
                G_No[3] = 0;
            } else if (chosen == BALL_MENU_CHOSE_EXIT) {
                Parry_The_Ball_Forget();
                G_No[3] = 0;

                // Row 2 of the mode select is TRAINING, and the menu opens on whatever this holds,
                // so the way out lands where this stage was asked for.
                Cursor_Y_Pos[0][0] = 2;

                // Out through the game's own session exit, which is what the training menu's EXIT
                // uses. From here rather than from the run-out below: nothing has been torn down
                // yet at this point, which is the state the menu task calls it in. Tried once from
                // the other side of System_all_clear_Level_B, it died on a multitexture that had
                // just gone. And return rather than break, so this case does not carry on into the
                // BG_move that follows it.
                Soft_Reset_Sub();
                return;
            }

            break;
        }

        if (Bonus_Sub()) {
            // Here, and not at the end of the stage's run-out, because Switch_Screen_Init on the
            // next line starts the fade to black that case 4 carries through. A menu put up after
            // it is drawn under a screen that has already gone dark -- correctly drawn, and
            // invisible for a reason that has nothing to do with drawing.
            if (Parry_The_Ball_Was_Requested()) {
                ball_menu_row = BALL_MENU_RETRY;
                G_No[3] = 1;
                break;
            }

            G_No[2] += 1;
            Cover_Timer = 24;
            Stop_Combo = 1;
            Switch_Screen_Init(0);
        }

        break;

    case 4:
        Bonus_Sub();

        if (Switch_Screen(0) != 0) {
            G_No[2] += 1;
            G_Timer = 3;
            SE_All_Off();
            Clear_Flash_No();
            effect_work_kill_mod_plcol();
        }

        break;

    default:
        Switch_Screen(0);
        Bonus_Sub();

        if (--G_Timer == 0) {
            Parry_The_Ball_Forget();
            Cover_Timer = 24;
            Suicide[0] = 1;
            System_all_clear_Level_B();
            G_No[1] = 10;
            G_No[2] = 0;
            G_No[3] = 0;
            E_No[0] = 9;
            E_No[1] = 0;
            E_No[2] = 0;
            E_No[3] = 0;
        }

        break;
    }

    BG_move();
}

s16 Bonus_Sub() {
    s16 x;

    mpp_w.inGame = true;
    Scene_Cut = Cut_Cut_Cut();
    Bonus_Game_Complete = 0;

    if (Game_pause != 0x81) {
        Game_timer += 1;
    }

    set_EXE_flag();
    Time_Control();

    if (Bonus_Type == 0x15) {
        Bonus_Game_Complete = Player_control_bonus();
    } else {
        Bonus_Game_Complete = Player_control_bonus2();
    }

    TATE00();
    x = 0;
    x = Game_Management();
    BG_Draw_System();
    reqPlayerDraw();
    Basic_Sub_Ex();
    hit_check_main_process();
    return x;
}

void Game10() {
    BG_Draw_System();
    Basic_Sub();
    Setup_Play_Type();

    switch (G_No[2]) {
    case 0:
        Switch_Screen(0);
        G_No[2] += 1;
        SC_No[0] = 0;
        SC_No[1] = 0;
        SC_No[2] = 0;
        SC_No[3] = 0;
        Stop_Combo = 0;
        init_slow_flag();
        break;

    case 1:
        if (After_Bonus() != 0) {
            G_No[2] += 1;
            Switch_Screen_Init(0);
        }

        break;

    default:
        After_Bonus();

        if (Switch_Screen(0) != 0) {
            Cover_Timer = 24;
            Game01_Sub();
            BGM_Stop();
            G_No[1] = 2;
            G_No[2] = 0;
            E_No[0] = 4;
            E_No[1] = 0;
            E_No[2] = 0;
            E_No[3] = 0;
            Bonus_Game_Flag = 0;
            Purge_texcash_of_list(3);
            Make_texcash_of_list(3);
        }

        break;
    }

    BG_move();
}

void Game11() {
    BG_Draw_System();
    Basic_Sub();
    Setup_Play_Type();

    switch (G_No[2]) {
    case 0:
        Switch_Screen(0);
        G_No[2] += 1;
        SC_No[0] = 0;
        SC_No[1] = 0;
        SC_No[2] = 0;
        SC_No[3] = 0;
        Stop_Combo = 0;
        Bonus_Type = 0;
        init_slow_flag();
        break;

    case 1:
        if (Next_Q()) {
            G_No[2] += 1;
            Switch_Screen_Init(0);
        }

        break;

    case 2:
        Next_Q();

        if (Switch_Screen(0) != 0) {
            Cover_Timer = 24;
            Game01_Sub();
            BGM_Stop();
            Purge_texcash_of_list(3);
            Make_texcash_of_list(3);

            if (Bonus_Type == 0) {
                G_No[1] = 2;
                G_No[2] = 0;
                E_No[0] = 4;
                E_No[1] = 0;
                E_No[2] = 0;
                E_No[3] = 0;
                Bonus_Game_Flag = 0;
            } else {
                G_No[1] = 9;
                G_No[2] = 0;
                G_No[3] = 0;
                E_No[0] = 4;
                E_No[1] = 0;
                E_No[2] = 0;
                E_No[3] = 0;
            }
        }

        break;

    case 3:
        G_No[2] += 1;
        SC_No[0] = 0;
        SC_No[1] = 0;
        SC_No[2] = 0;
        SC_No[3] = 0;
        Stop_Combo = 0;
        Bonus_Type = 0;
        init_slow_flag();
        Switch_Screen_Init(0);
        break;

    case 4:
        if (Switch_Screen(0) != 0) {
            G_No[2] = 1;
            Cover_Timer = 24;
        }

        break;
    }

    BG_move();
}

void Loop_Demo(struct _TASK* /* unused */) {
    if (Ck_Coin()) {
        Next_Title_Sub();
        return;
    }

    switch (G_No[1]) {
    case 0:
        G_No[1] += 1;
        G_No[2] = 0;
        G_No[3] = 0;
        D_No[0] = 0;
        D_No[1] = 0;
        D_No[2] = 0;
        D_No[3] = 0;
        E_No[1] = 99;
        Demo_PL_Index = 0;
        Demo_Stage_Index = 0;
        Select_Demo_Index = 0;
        Insert_Y = 23;
        Demo_Flag = 0;
        Play_Mode = 0;
        Replay_Status[0] = 0;
        Replay_Status[1] = 0;
        Present_Mode = 0;
        title_tex_flag = 0;
        Reset_Bootrom = 0;
        break;

    case 1:
        Basic_Sub();

        if (CAPCOM_Logo() != 0) {
            Loop_Demo_Sub();
            Insert_Y = 23;
            E_No[1] = 2;
            E_Timer = 1;
            return;
        }

        break;

    case 2:
        Basic_Sub();

        if (Title()) {
            Loop_Demo_Sub();
            Insert_Y = 17;
            D_No[0] = 1;
            return;
        }

        break;

    case 3:
        if (Play_Demo() != 0) {
            Switch_Screen(1);
            Loop_Demo_Sub();
            Rank_Type = 0;
            Demo_Type = 0;
            SsAllNoteOff();
            return;
        }

        break;

    case 4:
        Basic_Sub();

        if (Ranking() != 0) {
            Switch_Screen(1);
            Loop_Demo_Sub();
            return;
        }

        break;

    case 5:
        if (Play_Demo() != 0) {
            Loop_Demo_Sub();
            Demo_Type = 1;
            Rank_Type = 5;
            Demo_Type = 1;
            SsAllNoteOff();
            return;
        }

        break;

    case 6:
        Basic_Sub();

        if (Ranking() != 0) {
            Switch_Screen(1);
            Loop_Demo_Sub();
            System_all_clear_Level_B();
            Purge_mmtm_area(6);
            Game_pause = 0;
            G_No[1] = 1;
            E_No[1] = 99;
            return;
        }

        break;

    default:
        Switch_Screen(1);

        if (--Cover_Timer <= 0) {
            Next_Demo_Loop();
        }

        break;
    }
}

void Next_Demo_Loop() {
    G_No[0] = 1;
    G_No[1] = 1;
    G_No[2] = 0;
    D_No[0] = 0;
    D_No[1] = 0;
    D_No[2] = 0;
    D_No[3] = 0;
    E_No[0] = 0;
    E_No[1] = 99;
    E_No[2] = 0;
    E_No[3] = 0;
    Demo_PL_Index = 0;
    Demo_Stage_Index = 0;
    Select_Demo_Index = 0;
    Demo_Flag = 0;
    Present_Mode = 0;
    Game_pause = 0;
    Play_Mode = 0;
    Replay_Status[0] = 0;
    Replay_Status[1] = 0;
    System_all_clear_Level_B();
    Purge_mmtm_area(6);
}

void Loop_Demo_Sub() {
    G_No[1] += 1;
    G_No[2] = 0;
    D_No[0] = 0;
    D_No[1] = 0;
    D_No[2] = 0;
    D_No[3] = 0;
    E_No[1] = 1;
    Play_Game = 0;
    pulpul_stop();
    pp_operator_check_flag(1);
}

void Next_Title_Sub() {
    s16 ix;

    if (G_No[1] != 99) {
        SsAllNoteOff();
    }

    if (Demo_Flag == 0) {
        SsRequest(106);
    }

    TexRelease(600);
    TexRelease_OP();
    System_all_clear_Level_B();
    Purge_mmtm_area(6);
    G_Timer = 0;

    for (ix = 0; ix < 4; ix++) {
        vm_w.r_no[ix] = 0;
        G_No[ix] = 0;
        E_No[ix] = 0;
        D_No[ix] = 0;
        task[TASK_INIT].r_no[ix] = 0;
    }

    G_No[0] = 2;
    E_No[0] = 1;
    task[TASK_INIT].r_no[0] = 1;
    Demo_Flag = 1;
    Game_pause = 0;
    judge_flag = 0;
    Pause_Down = 0;
    Disp_Attack_Data = 0;
    seraph_flag = 0;
    End_Training = 0;
    Forbid_Reset = 0;
    Exec_Wipe = 0;
    Present_Mode = 1;
    Insert_Y = 23;
    Before_Select_Sub();
    cpReadyTask(TASK_ENTRY, Entry_Task);
}

void Time_Control() {
    count_cont_main();

    if ((Allow_a_battle_f == 0) || (Demo_Time_Stop != 0) || (Bonus_Game_Flag != 0)) {
        return;
    }

    if (Game_pause == 0x81) {
        return;
    }

    if (Control_Time >= Limit_Time) {
        Control_Time = Limit_Time;
    } else if (--Time_in_Time == 0) {
        Time_in_Time = 60;
        Control_Time += 1;
    }
}

s16 Ck_Coin() {
    s16 PL_id;

    switch (G_No[3]) {
    case 0:
        PL_id = -1;

        if (~p1sw_1 & p1sw_0 & (SWK_START | SWK_ATTACKS)) {
            PL_id = 0;
        } else if (~p2sw_1 & p2sw_0 & (SWK_START | SWK_ATTACKS)) {
            PL_id = 1;
        }

        if (PL_id == -1) {
            return 0;
        }

        ToneDown(0xFF, 0);
        Request_LDREQ_Break();
        G_No[3] = 1;
        plw[PL_id].wu.operator = 1;
        Operator_Status[PL_id] = 1;
        Champion = PL_id;
        plw[PL_id ^ 1].wu.operator = 0;
        Operator_Status[PL_id ^ 1] = 0;
        return 0;

    default:
    case 1:
        ToneDown(0xFF, 0);
        PL_id = Check_LDREQ_Break() ? 1 : 0;
        return PL_id ^ 1;
    }
}

void Before_Select_Sub() {
    s16 xx;

    Request_G_No = 0;
    Request_E_No = 0;
    Allow_a_battle_f = 0;
    Bonus_Type = 0;

    if (Demo_Flag == 0) {
        Control_Time = 2048;
        Round_Level = 7;
    } else {
        Control_Time = 481;
    }

    Super_Arts[0] = 0;
    Super_Arts[1] = 0;
    Exec_Wipe = 0;
    Fade_Flag = 0;
    Stock_Com_Color[0] = -1;
    Stock_Com_Arts[0] = -1;
    Stock_Com_Color[1] = -1;
    Stock_Com_Arts[1] = -1;
    Bonus_Game_Flag = 0;
    Combo_Demo_Flag = 0;
    paring_counter[0] = 0;
    paring_bonus_r[0] = 0;
    paring_counter[1] = 0;
    paring_bonus_r[1] = 0;
    Clear_Disp_Ranking(0);
    Clear_Disp_Ranking(1);
    Clear_Personal_Data(0);
    grade_check_work_1st_init(0, 0);
    grade_check_work_1st_init(0, 1);
    Clear_Personal_Data(1);
    grade_check_work_1st_init(1, 0);
    grade_check_work_1st_init(1, 1);
    Last_Player_id = Player_Number = -1;
    Round_Level = 3;
    Time_in_Time = 60;

    if (Mode_Type != MODE_NETWORK) {
        xx = system_timer;
        Random_ix16 = xx & 0x3F;
        Random_ix32 = xx & 0x7F;
    }
}

void Wait_Auto_Load(struct _TASK* /* unused */) {
    Basic_Sub();
    BG_Draw_System();
    bg_pos_hosei_sub2(0);
    Bg_Family_Set_appoint(0);
    BG_move_Ex(0);
}
