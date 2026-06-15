import { IconEdit, SvgWrapper } from '@theme';
import { useEditLink } from '@rspress/core/theme-original/components/EditLink/useEditLink.js';

function handleClick(e: React.MouseEvent, link: string) {
  e.preventDefault();
  e.stopPropagation();
  window.open(link, 'repopress-editor');
}

export function EditLink({ isOutline }: { isOutline?: boolean }) {
  const editLinkObj = useEditLink();
  if (!editLinkObj) return null;
  const { text, link } = editLinkObj;

  if (isOutline) {
    return (
      <a
        href={link}
        className="rp-outline__action-row rp-edit-link"
        onClick={(e) => handleClick(e, link)}
      >
        <SvgWrapper icon={IconEdit} width="16" height="16" />
        <span>{text}</span>
      </a>
    );
  }

  return (
    <a
      href={link}
      className="rp-edit-link"
      onClick={(e) => handleClick(e, link)}
    >
      {text}
    </a>
  );
}
