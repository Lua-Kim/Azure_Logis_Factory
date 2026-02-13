import ModuleCard from "../common/ModuleCard.jsx";

const CenterForm = ({ title = "CenterForm", children }) => (
  <ModuleCard title={title} description="Create or update centers">
    {children}
  </ModuleCard>
);

export default CenterForm;
