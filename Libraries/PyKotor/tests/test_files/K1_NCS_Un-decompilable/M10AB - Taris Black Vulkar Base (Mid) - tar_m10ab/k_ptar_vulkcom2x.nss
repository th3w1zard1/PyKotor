void main() {
	SetGlobalNumber("Tar_VulkarComputer", (GetGlobalNumber("Tar_VulkarComputer") | 2));
	int int2;
	object oTar10_lockturret;
	int2 = 0;
	while (1) {
		if (GetIsObjectValid(oTar10_lockturret = GetObjectByTag("tar10_lockturret", int2))) {
			ChangeToStandardFaction(oTar10_lockturret, 5);
			(int2++);
		}
	}
}
