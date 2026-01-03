
// Prototypes
int sub1();

int sub1() {
	int nGlobal = GetGlobalNumber("003EBO_BACKGROUND");
	switch (nGlobal) {
		case 0:
			return 2;
			break;
		case 1:
			return 10;
			break;
		case 2:
			return 9;
			break;
		case 3:
			return 6;
			break;
		case 4:
			return 1;
			break;
		case 5:
			return 0;
			break;
		case 6:
			return 3;
			break;
		case 7:
			return 4;
			break;
		case 8:
			return 2;
			break;
		case 9:
			return 5;
			break;
		case 10:
			return 2;
			break;
		default:
			return 2;
	}
	return 2;
}

void main() {
	if ((GetGlobalNumber("003EBO_Atton_Talk") <= 4)) {
		object oPC = GetFirstPC();
		AssignCommand(oPC, ClearAllActions());
		AssignCommand(OBJECT_SELF, ActionStartConversation(oPC, "galaxy", 0, 0, 1, "", "", "", "", "", "", 0, 0xFFFFFFFF, 0xFFFFFFFF, 0));
		return;
	}
	else {
		if ((GetGlobalNumber("003EBO_RETURN_DEST") == 4)) {
			if ((GetGlobalNumber("502OND_End_First") == 0)) {
				object object3 = GetFirstPC();
				AssignCommand(object3, ClearAllActions());
				AssignCommand(OBJECT_SELF, ActionStartConversation(object3, "galaxy2", 0, 0, 1, "", "", "", "", "", "", 0, 0xFFFFFFFF, 0xFFFFFFFF, 0));
				return;
			}
		}
		else {
			if ((GetGlobalNumber("003_IN_COMBAT") == 1)) {
				object object5 = GetFirstPC();
				AssignCommand(object5, ClearAllActions());
				AssignCommand(OBJECT_SELF, ActionStartConversation(object5, "galaxy", 0, 0, 1, "", "", "", "", "", "", 0, 0xFFFFFFFF, 0xFFFFFFFF, 0));
				return;
			}
		}
	}
	int int5 = 0;
	int5 = 0;
	while ((int5 < 11)) {
		SetPlanetAvailable(int5, 0);
		SetPlanetSelectable(int5, 0);
		(++int5);
	}
	if ((GetGlobalNumber("900MAL_Open") == 1)) {
		int5 = 0;
		while ((int5 < 11)) {
			{
				int int7 = int5;
				SetPlanetAvailable(int7, 1);
				if ((int5 == 5)) {
					SetPlanetSelectable(int7, 1);
				}
			}
			(int5++);
		}
	}
	else {
		if ((GetGlobalNumber("262TEL_Escape_Telos") == 1)) {
			int5 = 0;
			while ((int5 < 11)) {
				{
					int int9 = int5;
					if ((int5 != 5)) {
						SetPlanetAvailable(int9, 1);
					if ((int5 != 8)) {
						SetPlanetSelectable(int9, 1);
					}
					}
				}
				(int5++);
			}
			if ((GetGlobalNumber("401DXN_Visited") == 0)) {
				SetPlanetAvailable(1, 0);
				SetPlanetSelectable(1, 0);
			}
			else {
				SetPlanetSelectable(7, 0);
			}
		}
		else {
			SetPlanetAvailable(10, 1);
			SetPlanetSelectable(10, 1);
			SetPlanetAvailable(8, 1);
			SetPlanetSelectable(8, 0);
		}
		SetPlanetAvailable(4, 0);
		SetPlanetSelectable(4, 0);
		SetPlanetAvailable(9, 0);
		SetPlanetSelectable(9, 0);
		SetPlanetAvailable(2, 0);

        SetPlanetAvailable(15, 1);
		SetPlanetSelectable(15, 1); //Rhen Var?

		SetPlanetSelectable(2, 0); //PLANET_HARBINGER
		int int11 = sub1();
		if (((GetGlobalNumber("003EBO_BACKGROUND") == 8) || (GetGlobalNumber("003EBO_BACKGROUND") == 10))) {
			int11 = 2;
			SetPlanetAvailable(2, 1);
		}
		SetPlanetSelectable(int11, 0);
		ShowGalaxyMap(int11);
	}
}
