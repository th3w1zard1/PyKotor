int StartingConditional() {
	float float1 = 35.0;
	float float2 = 60.0;
	float float3 = 100.0;
	float float4 = 150.0;
	float float5 = 210.0;
	float float6;
	int int1;
	float float7;
	float float8;
	vector struct3;
	string string1;
	string string2;
	string string3;
	string string4;
	string string5;
	string string6;
	string string7;
	int nGlobal = GetGlobalNumber("MIN_RACE_GEAR");
	float float12 = IntToFloat(GetGlobalNumber("MIN_TENTH_GEAR"));
	object oEngine01;
	if (((GetTimeHour() < 24) && (nGlobal == (-5)))) {
		SetGlobalNumber("MIN_TIME_MIL", (GetTimeMillisecond() / 10));
		SetGlobalNumber("MIN_TIME_SEC", GetTimeSecond());
		SetGlobalNumber("MIN_TIME_MIN", GetTimeMinute());
		SetGlobalNumber("MIN_TIME_HOUR", GetTimeHour());
		nGlobal = (-4);
		SetGlobalNumber("MIN_RACE_GEAR", nGlobal);
	}
	int int10 = GetGlobalNumber("MIN_TIME_MIL");
	int int12 = GetGlobalNumber("MIN_TIME_SEC");
	int int14 = GetGlobalNumber("MIN_TIME_MIN");
	int int16 = GetGlobalNumber("MIN_TIME_HOUR");
	int int18 = (GetTimeMillisecond() / 10);
	int int20 = GetTimeSecond();
	int int22 = GetTimeMinute();
	int int24 = GetTimeHour();
	float float14 = 0.0;
	float14 = (float14 + ((((int10 / 100.0) + int12) + (int14 * 60)) + ((int16 * 2) * 60)));
	float float15 = 0.0;
	if ((int24 < int16)) {
		int24 = (int24 + 24);
	}
	float15 = (float15 + ((((int18 / 100.0) + int20) + (int22 * 60)) + ((int24 * 2) * 60)));
	float float16 = (float15 - float14);
	float6 = SWMG_GetPlayerSpeed();
	oEngine01 = GetObjectByTag("Wind", 0);
	int int26 = FloatToInt((float6 / 4.0));
	SoundObjectSetVolume(oEngine01, int26);
	if ((nGlobal < 0)) {
		if (((float16 > 0.1) && (nGlobal == (-4)))) {
			SWMG_PlayAnimation(OBJECT_SELF, "S3", 0, 0, 1);
			SetGlobalNumber("MIN_RACE_GEAR", (-3));
			oEngine01 = GetObjectByTag("PowerUp", 0);
			SoundObjectPlay(oEngine01);
			oEngine01 = GetObjectByTag("Idle", 0);
			SoundObjectPlay(oEngine01);
		}
		if (((float16 > 3.0) && (nGlobal == (-3)))) {
			oEngine01 = GetObjectByTag("S1", 0);
			SoundObjectPlay(oEngine01);
			SWMG_PlayAnimation(OBJECT_SELF, "S2", 0, 0, 1);
			SetGlobalNumber("MIN_RACE_GEAR", (-2));
		}
		if (((float16 > 4.0) && (nGlobal == (-2)))) {
			oEngine01 = GetObjectByTag("S1", 0);
			SoundObjectPlay(oEngine01);
			SWMG_PlayAnimation(OBJECT_SELF, "S1", 0, 0, 1);
			SetGlobalNumber("MIN_RACE_GEAR", (-1));
		}
		if (((float16 > 5.0) && (nGlobal == (-1)))) {
			oEngine01 = GetObjectByTag("Go", 0);
			SoundObjectPlay(oEngine01);
			SWMG_PlayAnimation(OBJECT_SELF, "SGo", 0, 0, 1);
			SetGlobalNumber("MIN_TIME_MIL", (GetTimeMillisecond() / 10));
			SetGlobalNumber("MIN_TIME_SEC", GetTimeSecond());
			SetGlobalNumber("MIN_TIME_MIN", GetTimeMinute());
			SetGlobalNumber("MIN_TIME_HOUR", GetTimeHour());
			SetGlobalNumber("MIN_RACE_GEAR", 0);
		}
	}
	float float18 = SWMG_GetPosition(OBJECT_SELF);
	if ((nGlobal > (-1))) {
		oEngine01 = GetObjectByTag("Wind", 0);
		int1 = FloatToInt(((float6 / 200.0) * 127.0));
		SoundObjectSetVolume(oEngine01, int1);
		if ((float18 > 3800.0)) {
			SWMG_RemoveAnimation(OBJECT_SELF, "cDistL1");
			SWMG_RemoveAnimation(OBJECT_SELF, "cDistL2");
			SWMG_RemoveAnimation(OBJECT_SELF, "cDistL3");
			SWMG_RemoveAnimation(OBJECT_SELF, "cDistL4");
			SWMG_RemoveAnimation(OBJECT_SELF, "cDistL5");
			SWMG_PlayAnimation(OBJECT_SELF, "cDistL0", 0, 0, 0);
			if ((nGlobal < 6)) {
				oEngine01 = GetObjectByTag("PowerDown01", 0);
				SoundObjectPlay(oEngine01);
				SWMG_SetPlayerMinSpeed(0.0);
				SWMG_SetPlayerMaxSpeed(0.0);
				SWMG_SetPlayerAccelerationPerSecond((float6 / 3.0));
				struct3 = SWMG_GetPosition(OBJECT_SELF);
				struct3.x = (struct3.x - 100.0);
				struct3.y = 0.0;
				struct3.z = 0.0;
				SWMG_SetPlayerTunnelNeg(struct3);
				SWMG_SetPlayerTunnelPos(struct3);
				SWMG_PlayAnimation(OBJECT_SELF, "downthrust", 0, 0, 1);
				SWMG_PlayAnimation(OBJECT_SELF, "endloop", 1, 0, 1);
				SetGlobalNumber("MIN_RACE_GEAR", 6);
				SWMG_PlayAnimation(OBJECT_SELF, "meter0", 0, 0, 1);
				oEngine01 = GetObjectByTag("Engine02", 0);
				SoundObjectFadeAndStop(oEngine01, 0.5);
				oEngine01 = GetObjectByTag("Engine03", 0);
				SoundObjectFadeAndStop(oEngine01, 0.5);
				oEngine01 = GetObjectByTag("Engine04", 0);
				SoundObjectFadeAndStop(oEngine01, 0.5);
				oEngine01 = GetObjectByTag("Engine05", 0);
				SoundObjectFadeAndStop(oEngine01, 0.5);
				oEngine01 = GetObjectByTag("Idle", 0);
				SoundObjectPlay(oEngine01);
				SetGlobalFadeOut(1.5, 1.0, 0.0, 0.0, 0.0);
				AssignCommand(GetFirstPC(), DelayCommand(3.0, StartNewModule("manm26ab", "from26mg", "", "", "", "", "", "")));
			}
		}
		else {
			string string8 = FloatToString(float16, 9, 2);
			int int33 = FloatToInt(float16);
			string string10 = IntToString(FloatToInt(((float16 - int33) * 100.0)));
			string string12 = IntToString(FloatToInt((((IntToFloat(int33) / 60.0) - (int33 / 60)) * 60.0)));
			string string14 = IntToString((int33 / 60));
			SetGlobalNumber("MAN_SWOOP_MIN", (int33 / 60));
			SetGlobalNumber("MAN_SWOOP_SEC", FloatToInt((((IntToFloat(int33) / 60.0) - (int33 / 60)) * 60.0)));
			SetGlobalNumber("MAN_SWOOP_MSEC", FloatToInt(((float16 - int33) * 100.0)));
			if ((GetStringLength(string10) == 1)) {
				string2 = string10;
				string3 = "0";
			}
			else {
				string2 = GetSubString(string10, 1, 1);
				string3 = GetSubString(string10, 0, 1);
			}
			if ((GetStringLength(string12) == 1)) {
				string4 = string12;
				string5 = "0";
			}
			else {
				string4 = GetSubString(string12, 1, 1);
				string5 = GetSubString(string12, 0, 1);
			}
			if ((GetStringLength(string14) == 1)) {
				string6 = string14;
				string7 = "0";
			}
			else {
				string6 = GetSubString(string14, 1, 1);
				string7 = GetSubString(string14, 0, 1);
			}
			string2 = ("MilSecOne" + string2);
			string3 = ("MilSecTen" + string3);
			string4 = ("SecOne" + string4);
			string5 = ("SecTen" + string5);
			string6 = ("MinOne" + string6);
			string7 = ("MinTen" + string7);
			SWMG_PlayAnimation(OBJECT_SELF, string2, 1, 0, 1);
			SWMG_PlayAnimation(OBJECT_SELF, string3, 1, 0, 1);
			SWMG_PlayAnimation(OBJECT_SELF, string4, 1, 0, 1);
			SWMG_PlayAnimation(OBJECT_SELF, string5, 1, 0, 1);
			SWMG_PlayAnimation(OBJECT_SELF, string6, 1, 0, 1);
			SWMG_PlayAnimation(OBJECT_SELF, string7, 1, 0, 1);
			if ((nGlobal == 0)) {
				float7 = 0.0;
			}
			else {
				if ((nGlobal == 1)) {
					float7 = ((float6 / float2) * 8.0);
				}
				else {
					if ((nGlobal == 2)) {
						float7 = (((float6 - float2) / (float3 - float2)) * 8.0);
					}
					else {
						if ((nGlobal == 3)) {
							float7 = (((float6 - float3) / (float4 - float3)) * 8.0);
						}
						else {
							if ((nGlobal == 4)) {
								float7 = (((float6 - float4) / (float5 - float4)) * 8.0);
							}
							else {
								if ((nGlobal == 5)) {
									float7 = ((((float6 - float5) / float5) * 2) * 8.0);
								}
							}
						}
					}
				}
			}
			if ((float7 < 0.0)) {
				float7 = 0.0;
			}
			else {
				if ((float7 > 9.0)) {
					float7 = 9.0;
				}
			}
			string1 = ("meter" + FloatToString(float7, 1, 0));
			string1 = GetSubString(string1, 0, (GetStringLength(string1) - 1));
			SWMG_PlayAnimation(OBJECT_SELF, string1, 0, 0, 1);
			if ((nGlobal == 1)) {
				oEngine01 = GetObjectByTag("Engine01", 0);
			}
			if ((nGlobal == 2)) {
				oEngine01 = GetObjectByTag("Engine02", 0);
			}
			if ((nGlobal == 3)) {
				oEngine01 = GetObjectByTag("Engine03", 0);
			}
			if ((nGlobal == 4)) {
				oEngine01 = GetObjectByTag("Engine04", 0);
			}
			if ((nGlobal == 5)) {
				oEngine01 = GetObjectByTag("Engine05", 0);
			}
			SoundObjectSetFixedVariance(oEngine01, ((float7 / 3.0) + 1));
			SetGlobalNumber("MIN_TENTH_GEAR", FloatToInt(float7));
		}
	}
	float8 = (((float6 - 50.0) / 150.0) * 5);
	if ((float8 < 1.0)) {
		float8 = 1.0;
	}
	else {
		if ((float8 > 5.0)) {
			float8 = 5.0;
		}
	}
	if ((float6 < 300.0)) {
		SWMG_SetLateralAccelerationPerSecond(float6);
	}
	else {
		SWMG_SetLateralAccelerationPerSecond(300.0);
	}
	if ((float6 < 70.0)) {
		int int44 = FloatToInt(((float6 / 70.0) * 10.0));
		string string24 = ("WakeSpeed0" + IntToString(int44));
		SWMG_PlayAnimation(OBJECT_SELF, string24, 1, 0, 1);
	}
	else {
		SWMG_PlayAnimation(OBJECT_SELF, "WakeSpeed09", 1, 0, 1);
	}
	if ((float6 < 150.0)) {
		SWMG_SetSpeedBlurEffect(0, 0.0);
	}
	else {
		SWMG_SetSpeedBlurEffect(1, ((float6 - 149.0) / 300.0));
	}
	string1 = ("camshake" + FloatToString(float8, 1, 0));
	string1 = GetSubString(string1, 0, (GetStringLength(string1) - 1));
	SWMG_PlayAnimation(OBJECT_SELF, string1, 1, 0, 0);
	if ((3800.0 > float18)) {
		string1 = ("cDistL" + FloatToString(float8, 1, 0));
		string1 = GetSubString(string1, 0, (GetStringLength(string1) - 1));
		SWMG_PlayAnimation(OBJECT_SELF, string1, 1, 0, 1);
	}
	return 0;
}

