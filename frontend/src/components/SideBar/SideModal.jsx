import React, {useEffect, useState} from "react";
import styles from "./styles.module.scss";
import {Modal, Select} from "antd";
import {useDispatch, useSelector} from "react-redux";
import {getAllPromts, postSystemPrompt, updateSystemPrompt} from "../../app/slices/User";

const SideModal = ({email, userSystemPrompt, popup, setPopup}) => {
	const dispatch = useDispatch();
	const systemPromptOptions = useSelector(s => s.auth.systemPrompts);
	const [systemPrompt, setSystemPrompt] = useState(userSystemPrompt);

	useEffect(() => {
		dispatch(getAllPromts());
	}, [dispatch]);

	if (!systemPromptOptions?.length) {
		return null;
	}

	const onSubmitClick = () => {
		dispatch(updateSystemPrompt(systemPrompt));
		dispatch(postSystemPrompt({system_prompt_id: systemPrompt.value}));
		setPopup(false);
	};

	const formattedOptions = systemPromptOptions?.map(prompt => ({
		value: prompt.id,
		label: prompt.name,
		promptText: prompt.text,
	}));
	return (
		<Modal visible={popup} onCancel={() => setPopup(false)} onOk={onSubmitClick}>
			<div className={styles.modalCont}>
				<div className={styles.profileIcon} />
				<div className={styles.secondaryTitle}>{email}</div>
				<div className={styles.selectCont}>
					<div>Системный промпт</div>
					<Select className={styles.select} placeholder='Выберите системный промпт' options={formattedOptions} value={systemPrompt.id} onChange={value => setSystemPrompt(value)} />
				</div>
			</div>
		</Modal>
	);
};

export default SideModal;
