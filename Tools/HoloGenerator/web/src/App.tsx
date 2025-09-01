import React, { useState, useCallback, useMemo } from 'react';
import styled from 'styled-components';
import { FileContent, DiffResult, GeneratedConfig } from './types';
import { createDiffResult, generateChangesIni } from './utils/diffUtils';

const AppContainer = styled.div`
  height: 100vh;
  display: flex;
  flex-direction: column;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif;
`;

const Header = styled.header`
  background: #24292e;
  color: white;
  padding: 16px 24px;
  text-align: center;
`;

const Title = styled.h1`
  margin: 0 0 8px 0;
  font-size: 28px;
  font-weight: 600;
`;

const Subtitle = styled.p`
  margin: 0;
  font-size: 16px;
  opacity: 0.8;
`;

const MainContent = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 20px;
  gap: 20px;
`;

const EditorContainer = styled.div`
  display: flex;
  gap: 20px;
  flex: 1;
`;

const EditorBox = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
`;

const EditorLabel = styled.label`
  font-weight: 600;
  margin-bottom: 8px;
  color: #24292e;
`;

const TextArea = styled.textarea`
  flex: 1;
  min-height: 300px;
  border: 1px solid #e1e5e9;
  border-radius: 6px;
  padding: 12px;
  font-family: 'SFMono-Regular', 'Consolas', 'Liberation Mono', monospace;
  font-size: 13px;
  line-height: 1.45;
  resize: vertical;
  
  &:focus {
    outline: none;
    border-color: #0969da;
    box-shadow: 0 0 0 3px rgba(9, 105, 218, 0.1);
  }
`;

const ToolbarContainer = styled.div`
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 0;
  border-bottom: 1px solid #e1e5e9;
`;

const Button = styled.button<{ variant?: 'primary' | 'secondary' }>`
  padding: 8px 16px;
  border-radius: 6px;
  border: 1px solid;
  font-size: 14px;
  cursor: pointer;
  font-weight: 500;
  
  ${props => props.variant === 'primary' ? `
    background: #0969da;
    color: white;
    border-color: #0969da;
    
    &:hover {
      background: #0860ca;
      border-color: #0860ca;
    }
    
    &:disabled {
      background: #94a3b8;
      border-color: #94a3b8;
      cursor: not-allowed;
    }
  ` : `
    background: #f6f8fa;
    color: #24292e;
    border-color: #d1d9e0;
    
    &:hover {
      background: #e1e7ed;
    }
    
    &:disabled {
      background: #f6f8fa;
      color: #656d76;
      cursor: not-allowed;
    }
  `}
`;

const ResultContainer = styled.div`
  border: 1px solid #e1e5e9;
  border-radius: 6px;
  overflow: hidden;
`;

const ResultHeader = styled.div`
  background: #f6f8fa;
  padding: 12px 16px;
  border-bottom: 1px solid #e1e5e9;
  font-weight: 600;
`;

const ResultContent = styled.pre`
  margin: 0;
  padding: 16px;
  background: #f8f9fa;
  font-family: 'SFMono-Regular', 'Consolas', 'Liberation Mono', monospace;
  font-size: 13px;
  line-height: 1.45;
  white-space: pre-wrap;
  max-height: 400px;
  overflow-y: auto;
`;

export const App: React.FC = () => {
  const [originalContent, setOriginalContent] = useState('');
  const [modifiedContent, setModifiedContent] = useState('');
  const [originalFileName, setOriginalFileName] = useState('original.txt');
  const [modifiedFileName, setModifiedFileName] = useState('modified.txt');
  const [diffs, setDiffs] = useState<DiffResult[]>([]);
  const [generatedConfig, setGeneratedConfig] = useState<GeneratedConfig | null>(null);

  const canCompare = useMemo(() => {
    return originalContent.trim() && modifiedContent.trim() && 
           originalContent !== modifiedContent;
  }, [originalContent, modifiedContent]);

  const handleCompare = useCallback(() => {
    if (!canCompare) return;

    const originalFile: FileContent = {
      name: originalFileName,
      content: originalContent,
      type: 'text'
    };

    const modifiedFile: FileContent = {
      name: modifiedFileName,
      content: modifiedContent,
      type: 'text'
    };

    const diffResult = createDiffResult(originalFile, modifiedFile);
    setDiffs(prev => [...prev, diffResult]);
  }, [originalContent, modifiedContent, originalFileName, modifiedFileName, canCompare]);

  const handleGenerateConfig = useCallback(() => {
    if (diffs.length === 0) return;
    
    const config = generateChangesIni(diffs);
    setGeneratedConfig(config);
  }, [diffs]);

  const handleClear = useCallback(() => {
    setOriginalContent('');
    setModifiedContent('');
    setDiffs([]);
    setGeneratedConfig(null);
  }, []);

  const handleCopyConfig = useCallback(async () => {
    if (!generatedConfig) return;
    
    try {
      await navigator.clipboard.writeText(generatedConfig.content);
      alert('Configuration copied to clipboard!');
    } catch (error) {
      console.error('Failed to copy to clipboard:', error);
    }
  }, [generatedConfig]);

  return (
    <AppContainer>
      <Header>
        <Title>HoloGenerator</Title>
        <Subtitle>KOTOR Configuration Generator for HoloPatcher</Subtitle>
      </Header>
      
      <MainContent>
        <ToolbarContainer>
          <Button variant="primary" onClick={handleCompare} disabled={!canCompare}>
            Compare Files
          </Button>
          <Button onClick={handleGenerateConfig} disabled={diffs.length === 0}>
            Generate changes.ini ({diffs.length} diffs)
          </Button>
          <Button onClick={handleClear}>
            Clear All
          </Button>
          {generatedConfig && (
            <Button onClick={handleCopyConfig}>
              Copy Configuration
            </Button>
          )}
        </ToolbarContainer>

        <EditorContainer>
          <EditorBox>
            <EditorLabel>
              Original File:
              <input
                type="text"
                value={originalFileName}
                onChange={(e) => setOriginalFileName(e.target.value)}
                style={{ marginLeft: '8px', padding: '4px 8px', border: '1px solid #d1d9e0', borderRadius: '4px' }}
              />
            </EditorLabel>
            <TextArea
              value={originalContent}
              onChange={(e) => setOriginalContent(e.target.value)}
              placeholder="Paste your original file content here..."
            />
          </EditorBox>

          <EditorBox>
            <EditorLabel>
              Modified File:
              <input
                type="text"
                value={modifiedFileName}
                onChange={(e) => setModifiedFileName(e.target.value)}
                style={{ marginLeft: '8px', padding: '4px 8px', border: '1px solid #d1d9e0', borderRadius: '4px' }}
              />
            </EditorLabel>
            <TextArea
              value={modifiedContent}
              onChange={(e) => setModifiedContent(e.target.value)}
              placeholder="Paste your modified file content here..."
            />
          </EditorBox>
        </EditorContainer>

        {generatedConfig && (
          <ResultContainer>
            <ResultHeader>
              Generated changes.ini ({generatedConfig.sections.length} sections)
            </ResultHeader>
            <ResultContent>
              {generatedConfig.content}
            </ResultContent>
          </ResultContainer>
        )}
      </MainContent>
    </AppContainer>
  );
};