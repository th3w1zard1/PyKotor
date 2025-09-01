import { diffLines, diffWordsWithSpace } from 'diff';
import { FileContent, DiffResult, GeneratedConfig, ConfigSection, WordDiffPart } from '../types';

export const generateDiffId = (): string => {
  const timestamp = Date.now();
  const random = Math.random().toString(36).substr(2, 9);
  return `diff_${timestamp}_${random}`;
};

export const detectFileType = (fileName: string, content: string): FileContent['type'] => {
  const extension = fileName.toLowerCase().split('.').pop() || '';
  
  // Check content for specific patterns
  if (content.includes('[Settings]') || content.includes('[InstallList]')) {
    return 'ini';
  }
  
  if (content.startsWith('2DA V2.b') || extension === '2da') {
    return '2da';
  }
  
  if (content.includes('TLK Language:') || extension === 'tlk') {
    return 'tlk';
  }
  
  // GFF extensions
  const gffExtensions = ['gff', 'utc', 'uti', 'dlg', 'are', 'git', 'ifo', 'jrl'];
  if (gffExtensions.includes(extension)) {
    return extension as FileContent['type'];
  }
  
  // Other specific extensions
  if (['ssf', 'lip'].includes(extension)) {
    return extension as FileContent['type'];
  }
  
  return 'text';
};

export const generateUnifiedDiff = (original: string, modified: string, fileName: string): string => {
  if (original === modified) {
    return 'No differences found';
  }
  
  const diff = diffLines(original, modified);
  
  const result: string[] = [
    `--- original/${fileName}`,
    `+++ modified/${fileName}`
  ];
  
  for (const part of diff) {
    const lines = part.value.split('\n');
    if (lines[lines.length - 1] === '') {
      lines.pop(); // Remove empty last line
    }
    
    for (const line of lines) {
      if (part.added) {
        result.push(`+${line}`);
      } else if (part.removed) {
        result.push(`-${line}`);
      } else {
        result.push(` ${line}`);
      }
    }
  }
  
  return result.join('\n');
};

export const generateWordDiff = (original: string, modified: string): WordDiffPart[] => {
  return diffWordsWithSpace(original, modified);
};

export const createDiffResult = (originalFile: FileContent, modifiedFile: FileContent): DiffResult => {
  const diffContent = generateUnifiedDiff(originalFile.content, modifiedFile.content, originalFile.name);
  
  return {
    id: generateDiffId(),
    originalFile,
    modifiedFile,
    diffContent,
    timestamp: new Date()
  };
};

export const generateChangesIni = (diffs: DiffResult[]): GeneratedConfig => {
  const sections: ConfigSection[] = [];
  
  // Always start with Settings section
  sections.push({
    name: 'Settings',
    entries: {
      'WindowCaption': 'Generated Mod Configuration',
      'ConfirmMessage': 'This mod was generated from a KOTOR installation diff using HoloGenerator.',
      'ExecutableType': '1'
    }
  });
  
  const gffFiles: string[] = [];
  const twodaFiles: string[] = [];
  const tlkEntries: Record<string, string> = {};
  const ssfFiles: string[] = [];
  const installFiles: string[] = [];
  
  // Process each diff
  diffs.forEach((diff, index) => {
    const fileName = diff.modifiedFile.name;
    const fileType = diff.modifiedFile.type;
    
    switch (fileType) {
      case 'gff':
      case 'utc':
      case 'uti':
      case 'dlg':
      case 'are':
      case 'git':
      case 'ifo':
      case 'jrl':
        gffFiles.push(fileName);
        // Add GFF file section with basic modification
        sections.push({
          name: fileName,
          entries: {
            'ModifyField1': 'FieldModification1'
          }
        });
        break;
        
      case '2da':
        twodaFiles.push(fileName);
        // Add 2DA file section with basic row modification
        sections.push({
          name: fileName,
          entries: {
            'ChangeRow1': 'RowModification1'
          }
        });
        break;
        
      case 'tlk':
        // Extract TLK entries from diff
        const tlkMatches = diff.diffContent.match(/\+Entry (\d+):/g);
        if (tlkMatches) {
          tlkMatches.forEach(match => {
            const entryNum = match.match(/(\d+)/)?.[1];
            if (entryNum) {
              tlkEntries[`StrRef${entryNum}`] = 'Modified';
            }
          });
        }
        break;
        
      case 'ssf':
        ssfFiles.push(fileName);
        // Add SSF file section
        sections.push({
          name: fileName,
          entries: {
            'Sound1': 'NewSound1'
          }
        });
        break;
        
      default:
        // For other file types, add to install list
        installFiles.push(fileName);
        break;
    }
  });
  
  // Add list sections
  if (gffFiles.length > 0) {
    const gffEntries: Record<string, string> = {};
    gffFiles.forEach((file, index) => {
      gffEntries[`File${index + 1}`] = file;
    });
    sections.push({
      name: 'GFFList',
      entries: gffEntries
    });
  }
  
  if (twodaFiles.length > 0) {
    const twodaEntries: Record<string, string> = {};
    twodaFiles.forEach((file, index) => {
      twodaEntries[`File${index + 1}`] = file;
    });
    sections.push({
      name: '2DAList',
      entries: twodaEntries
    });
  }
  
  if (Object.keys(tlkEntries).length > 0) {
    sections.push({
      name: 'TLKList',
      entries: tlkEntries
    });
  }
  
  if (ssfFiles.length > 0) {
    const ssfEntries: Record<string, string> = {};
    ssfFiles.forEach((file, index) => {
      ssfEntries[`File${index + 1}`] = file;
    });
    sections.push({
      name: 'SSFList',
      entries: ssfEntries
    });
  }
  
  if (installFiles.length > 0) {
    const installEntries: Record<string, string> = {};
    installFiles.forEach((file, index) => {
      installEntries[`File${index + 1}`] = 'Override';
    });
    sections.push({
      name: 'InstallList',
      entries: installEntries
    });
    
    // Add Override section
    const overrideEntries: Record<string, string> = {};
    installFiles.forEach((file, index) => {
      overrideEntries[`File${index + 1}`] = file;
    });
    sections.push({
      name: 'Override',
      entries: overrideEntries
    });
  }
  
  // Generate the final content
  const content = sections.map(section => {
    const lines = [`[${section.name}]`];
    Object.entries(section.entries).forEach(([key, value]) => {
      lines.push(`${key}=${value}`);
    });
    return lines.join('\n');
  }).join('\n\n');
  
  return {
    sections,
    content,
    timestamp: new Date()
  };
};