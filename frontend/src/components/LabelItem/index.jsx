import React from "react";

const LabelItem = ({handler, label}) => {
	return <div onClick={handler}>{label}</div>;
};

export default LabelItem;
