export interface FileContent {
  name: string;
  content: string;
  type: 'gff' | 'utc' | 'uti' | 'dlg' | 'are' | 'git' | 'ifo' | 'jrl' | '2da' | 'tlk' | 'ssf' | 'lip' | 'ini' | 'text';
}

export interface DiffResult {
  id: string;
  originalFile: FileContent;
  modifiedFile: FileContent;
  diffContent: string;
  timestamp: Date;
}

export interface HistoryState {
  diffs: DiffResult[];
  currentIndex: number;
}

export interface ConfigSection {
  name: string;
  entries: Record<string, string>;
}

export interface GeneratedConfig {
  sections: ConfigSection[];
  content: string;
  timestamp: Date;
}

export interface WordDiffPart {
  value: string;
  added?: boolean;
  removed?: boolean;
}