const ModuleCard = ({ title, description, children }) => (
  <div className="module-card">
    <div className="module-card__header">
      <h3>{title}</h3>
      {description ? <p>{description}</p> : null}
    </div>
    <div className="module-card__body">{children}</div>
  </div>
);

export default ModuleCard;
