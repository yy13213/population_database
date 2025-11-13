ALTER TABLE marriage_info
  ADD CONSTRAINT fk_marriage_male
    FOREIGN KEY (male_id_no) REFERENCES population(id_no)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,
  ADD CONSTRAINT fk_marriage_female
    FOREIGN KEY (female_id_no) REFERENCES population(id_no)
    ON UPDATE CASCADE
    ON DELETE RESTRICT;
