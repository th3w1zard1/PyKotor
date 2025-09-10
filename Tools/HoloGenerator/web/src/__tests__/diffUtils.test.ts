import { 
  generateDiffId, 
  detectFileType, 
  generateUnifiedDiff, 
  createDiffResult,
  generateChangesIni 
} from '../utils/diffUtils';
import { FileContent, DiffResult } from '../types';

describe('diffUtils', () => {
  describe('generateDiffId', () => {
    it('should generate unique IDs', () => {
      const id1 = generateDiffId();
      const id2 = generateDiffId();
      
      expect(id1).not.toBe(id2);
      expect(id1).toMatch(/^diff_\d+_[a-z0-9]+$/);
    });
  });

  describe('detectFileType', () => {
    it('should detect INI files', () => {
      expect(detectFileType('test.ini', '[Settings]')).toBe('ini');
      expect(detectFileType('changes.txt', '[InstallList]')).toBe('ini');
    });

    it('should detect 2DA files', () => {
      expect(detectFileType('test.2da', '2DA V2.b')).toBe('2da');
      expect(detectFileType('appearance.2da', 'some content')).toBe('2da');
    });

    it('should detect TLK files', () => {
      expect(detectFileType('dialog.tlk', 'TLK Language: English')).toBe('tlk');
      expect(detectFileType('test.tlk', 'some content')).toBe('tlk');
    });

    it('should detect GFF files', () => {
      expect(detectFileType('test.utc', 'content')).toBe('utc');
      expect(detectFileType('test.dlg', 'content')).toBe('dlg');
      expect(detectFileType('test.are', 'content')).toBe('are');
    });

    it('should default to text for unknown types', () => {
      expect(detectFileType('unknown.xyz', 'content')).toBe('text');
      expect(detectFileType('readme.txt', 'content')).toBe('text');
    });
  });

  describe('generateUnifiedDiff', () => {
    it('should generate diff for different content', () => {
      const original = 'line1\nline2\nline3';
      const modified = 'line1\nmodified line2\nline3';
      
      const diff = generateUnifiedDiff(original, modified, 'test.txt');
      
      expect(diff).toContain('--- original/test.txt');
      expect(diff).toContain('+++ modified/test.txt');
      expect(diff).toContain('+modified line2');
      expect(diff).toContain('-line2');
    });

    it('should handle identical content', () => {
      const content = 'line1\nline2\nline3';
      
      const diff = generateUnifiedDiff(content, content, 'test.txt');
      
      expect(diff).toBe('No differences found');
    });

    it('should handle empty content', () => {
      const diff = generateUnifiedDiff('', 'new content', 'test.txt');
      
      expect(diff).toContain('+new content');
    });
  });

  describe('createDiffResult', () => {
    it('should create a complete diff result', () => {
      const originalFile: FileContent = {
        name: 'test.txt',
        content: 'original content',
        type: 'text'
      };
      
      const modifiedFile: FileContent = {
        name: 'test.txt',
        content: 'modified content',
        type: 'text'
      };
      
      const result = createDiffResult(originalFile, modifiedFile);
      
      expect(result.id).toBeDefined();
      expect(result.originalFile).toBe(originalFile);
      expect(result.modifiedFile).toBe(modifiedFile);
      expect(result.diffContent).toContain('original content');
      expect(result.diffContent).toContain('modified content');
      expect(result.timestamp).toBeInstanceOf(Date);
    });
  });

  describe('generateChangesIni', () => {
    it('should generate basic settings section', () => {
      const config = generateChangesIni([]);
      
      expect(config.sections).toHaveLength(1);
      expect(config.sections[0].name).toBe('Settings');
      expect(config.content).toContain('[Settings]');
      expect(config.content).toContain('WindowCaption=Generated Mod Configuration');
    });
  });
});