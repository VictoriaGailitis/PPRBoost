import React, {useEffect, useState} from "react";
import styles from "./styles.module.scss";
import {Menu} from "antd";
import {CloseOutlined, MessageOutlined} from "@ant-design/icons";
import {useDispatch, useSelector} from "react-redux";
import classNames from "classnames";
import {useNavigate, useParams} from "react-router-dom";
import {deleteChat, getAllChats} from "../../app/slices/List";
import SideModal from "./SideModal";

const SideBar = () => {
	const overlay = useSelector(s => s.layout.overlay);
	const lists = useSelector(s => s.list.list);
	const dispatch = useDispatch();
	const user = useSelector(s => s.auth);
	const navigate = useNavigate();
	const {id} = useParams();
	const [popup, setPopup] = useState(false);

	useEffect(() => {
		dispatch(getAllChats());
	}, [dispatch]);

	const onListClick = id => {
		navigate(`/${id}`);
	};

	const onPlusCLick = () => {
		navigate(`/`);
	};
	return (
		<>
			<div className={classNames(styles.sideBar, overlay && styles.open)}>
				<div className={styles.top}>
					<div className={styles.title}>ТендерЧат</div>
					<div className={styles.secondTitle}>
						<div>Чаты</div>
						<div className={styles.addBtn} onClick={onPlusCLick}></div>
					</div>
					{!!lists.length && (
						<Menu
							className={styles.menuList}
							selectedKeys={id ? [id] : []}
							items={lists.map(el => ({
								label: (
									<div className={styles.labelItem}>
										<div>{el.title}</div>
										<CloseOutlined onClick={() => dispatch(deleteChat(el.id))} />
									</div>
								),
								key: el.id,
								icon: <MessageOutlined />,
								onClick: () => {
									onListClick(el.id);
								},
							}))}
						/>
					)}
				</div>
				<div className={styles.profile} onClick={() => setPopup(true)}>
					<div className={styles.avatar}></div>
					<div>{user.email}</div>
				</div>
			</div>
			<SideModal popup={popup} setPopup={setPopup} email={user.email} userSystemPrompt={user.systemPrompt} />
		</>
	);
};

export default SideBar;
