import { useHotkeys } from 'react-hotkeys-hook';
import { useHistory } from './useHistory';

export const useKeyboardShortcuts = () => {
  const { undo, redo, canUndo, canRedo } = useHistory();

  useHotkeys('ctrl+z', () => {
    if (canUndo) {
      undo();
    }
  }, [canUndo, undo]);

  useHotkeys('ctrl+y', () => {
    if (canRedo) {
      redo();
    }
  }, [canRedo, redo]);

  useHotkeys('ctrl+shift+z', () => {
    if (canRedo) {
      redo();
    }
  }, [canRedo, redo]);

  return { undo, redo, canUndo, canRedo };
};