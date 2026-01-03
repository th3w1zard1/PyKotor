// Globals
	int intGLOB_1 = 3;
	int intGLOB_2 = 4;
	int intGLOB_3 = 5;
	int intGLOB_4 = 6;
	int intGLOB_5 = 1;
	int intGLOB_6 = 2;
	int intGLOB_7 = 3;
	int intGLOB_8 = 4;
	int intGLOB_9 = 5;
	int intGLOB_10 = 6;
	int intGLOB_11 = 7;
	int intGLOB_12 = 8;
	int intGLOB_13 = 9;
	int intGLOB_14 = 10;
	int intGLOB_15 = 11;
	int intGLOB_16 = 12;
	int intGLOB_17 = 13;
	int intGLOB_18 = 14;
	int intGLOB_19 = 15;
	int intGLOB_20 = 16;
	int intGLOB_21 = 17;
	int intGLOB_22 = 18;
	int intGLOB_23 = 19;
	int intGLOB_24 = 20;
	int intGLOB_25 = 21;
	int intGLOB_26 = 22;
	int intGLOB_27 = 23;
	int intGLOB_28 = 24;
	int intGLOB_29 = 25;
	int intGLOB_30 = 26;
	int intGLOB_31 = 27;
	int intGLOB_32 = 28;
	int intGLOB_33 = 29;
	int intGLOB_34 = 59;
	int intGLOB_35 = 0;
	int intGLOB_36 = 1;
	int intGLOB_37 = 2;
	int intGLOB_38 = 34;
	int intGLOB_39 = 35;
	int intGLOB_40 = 36;
	int intGLOB_41 = 37;
	int intGLOB_42 = 38;
	int intGLOB_43 = 39;
	int intGLOB_44 = 41;
	int intGLOB_45 = 42;
	int intGLOB_46 = 46;
	int intGLOB_47 = 47;
	int intGLOB_48;
	int intGLOB_49;
	int intGLOB_50;
	object objectGLOB_1;
	int intGLOB_51;
	int intGLOB_52;
	int intGLOB_53;
	int intGLOB_54;
	int intGLOB_55;
	int intGLOB_56 = 1;
	int intGLOB_57 = 2;
	int intGLOB_58 = 3;
	int intGLOB_59 = 20;
	int intGLOB_60 = 21;
	int intGLOB_61 = 22;
	int intGLOB_62 = 23;
	int intGLOB_63 = 24;
	int intGLOB_64 = 25;
	int intGLOB_65 = 26;
	int intGLOB_66 = 27;
	int intGLOB_67 = 28;
	int intGLOB_68 = 29;
	int intGLOB_69 = 30;
	int intGLOB_70 = 31;
	int intGLOB_71 = 32;
	int intGLOB_72 = 33;
	int intGLOB_73 = 40;
	int intGLOB_74 = 43;
	int intGLOB_75 = 44;
	int intGLOB_76 = 45;
	int intGLOB_77 = 48;
	int intGLOB_78 = 49;
	int intGLOB_79 = 50;
	int intGLOB_80 = 51;
	int intGLOB_81 = 52;
	int intGLOB_82 = 53;
	int intGLOB_83 = 54;
	int intGLOB_84 = 55;
	int intGLOB_85 = 56;
	int intGLOB_86 = 57;
	int intGLOB_87 = 58;
	int intGLOB_88 = 60;
	int intGLOB_89 = 61;
	int intGLOB_90 = 62;
	int intGLOB_91 = 63;
	int intGLOB_92 = 1;
	int intGLOB_93 = 2;
	int intGLOB_94 = 3;
	int intGLOB_95 = 4;
	int intGLOB_96 = 0;
	int intGLOB_97 = 1;
	int intGLOB_98 = 2;
	int intGLOB_99 = 3;
	int intGLOB_100 = 4;
	int intGLOB_101 = 5;
	int intGLOB_102 = 6;
	int intGLOB_103 = 7;
	int intGLOB_104 = 8;
	int intGLOB_105 = 9;
	int intGLOB_106 = 10;
	int intGLOB_107 = 11;
	int intGLOB_108 = 12;
	int intGLOB_109 = 13;
	int intGLOB_110 = 14;
	int intGLOB_111 = 15;
	int intGLOB_112 = 16;
	int intGLOB_113 = 17;
	int intGLOB_114 = 18;
	int intGLOB_115 = 19;
	int intGLOB_116 = 1100;

// Prototypes
void sub3(object objectParam1, int intParam2);
int sub2(object objectParam1);
void sub1(string stringParam1, int intParam2, int intParam3, float floatParam4);

void sub3(object objectParam1, int intParam2) {
	if (GetIsObjectValid(objectParam1)) {
		if (((intParam2 == 1) || (intParam2 == 0))) {
			SetLocalBoolean(objectParam1, intGLOB_106, intParam2);
		}
	}
}

int sub2(object objectParam1) {
	int nLocalBool;
	if (GetIsObjectValid(objectParam1)) {
		nLocalBool = GetLocalBoolean(objectParam1, intGLOB_106);
		if ((nLocalBool > 0)) {
			return 1;
		}
	}
	return 0;
}

void sub1(string stringParam1, int intParam2, int intParam3, float floatParam4) {
	AurPostString(stringParam1, intParam2, intParam3, floatParam4);
}

void main() {
	int int1 = GetUserDefinedEventNumber();
	if ((int1 == 1001)) {
		int nGlobal = GetGlobalNumber("UNK_TEMPLEALARM");
		if ((nGlobal > 0)) {
			(nGlobal--);
			SetGlobalNumber("UNK_TEMPLEALARM", nGlobal);
		}
		else {
			if (GetIsObjectValid(GetAttackTarget(OBJECT_SELF))) {
				int int6;
				int int7;
				object oNearestUnk44_sithguard;
				sub1("SUMMONING GUARDS", 5, 6, 6.0);
				int7 = 0;
				while ((int7 < 2)) {
					int6 = 0;
					do {
						oNearestUnk44_sithguard = GetNearestObjectByTag("unk44_sithguard", OBJECT_SELF, (int6 + 1));
						if ((!GetIsObjectValid(oNearestUnk44_sithguard))) {
							sub1("BAD GUARD", 5, 7, 1.0);
						}
						else {
							if (((GetDistanceBetween(OBJECT_SELF, oNearestUnk44_sithguard) < 30.0) && (!sub2(oNearestUnk44_sithguard)))) {
								sub1(("GUARD SUMMONED - " + IntToString(int6)), 5, (7 + int7), 1.0);
								sub3(oNearestUnk44_sithguard, 1);
								AssignCommand(oNearestUnk44_sithguard, ActionForceMoveToObject(OBJECT_SELF, 1, 1.0, 10.0));
								oNearestUnk44_sithguard = OBJECT_INVALID;
							}
							else {
								(int6++);
							}
						}
						if (GetIsObjectValid(oNearestUnk44_sithguard)) {
						}
						else {
							(int7++);
							SetGlobalNumber("UNK_TEMPLEALARM", 4);
							break;
							return;
							if ((oNearestUnk44_sithguard == 1002)) {
							}
							else {
								if ((oNearestUnk44_sithguard == 1003)) {
								}
								else {
									if ((oNearestUnk44_sithguard == 1004)) {
									}
									else {
										if ((oNearestUnk44_sithguard == 1005)) {
										}
										else {
											if ((oNearestUnk44_sithguard == 1006)) {
											}
											else {
												if ((oNearestUnk44_sithguard == 1007)) {
												}
												else {
													if ((oNearestUnk44_sithguard == 1008)) {
													}
													else {
														if ((oNearestUnk44_sithguard == 1009)) {
														}
														else {
															if ((oNearestUnk44_sithguard == 1010)) {
															}
														}
													}
												}
											}
										}
									}
								}
							}
						}
						if (1) {
						}
						else {
							break;
							return;
						}
						if (1) {
						}
						else {
							break;
							return;
						}
						if (1) {
						}
						else {
							break;
							return;
						}
						if (1) {
						}
						else {
							break;
							return;
						}
					} while (1);
				}
			}
		}
	}
}
